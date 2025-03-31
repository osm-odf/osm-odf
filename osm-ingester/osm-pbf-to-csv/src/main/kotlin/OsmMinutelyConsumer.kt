import java.io.File
import java.io.FileWriter
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Instant
import java.time.ZoneId
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import javax.xml.parsers.DocumentBuilderFactory
import org.w3c.dom.Element
import org.w3c.dom.NodeList
import org.xml.sax.InputSource
import java.io.StringReader

/**
 * Kotlin implementation of the OSM Minutely Changes consumer
 * This fetches and processes OpenStreetMap minutely updates from the Overpass API
 */
class OsmMinutelyConsumer {
    // Environment variables
    private val verbose = System.getenv("VERBOSE") == "1"
    private val processNodes = System.getenv("NODES") == "1"
    private val processWays = System.getenv("WAYS") == "1"
    private val processRelations = System.getenv("RELATIONS") == "1"
    private val processTags = System.getenv("TAGS") == "1"
    private var latestChangeset = System.getenv("ODF_ETAG")?.toLongOrNull() ?: 0L
    private val etagPath = System.getenv("ODF_NEW_ETAG_PATH")
    
    // Current epoch in seconds
    private val currentEpoch = Instant.now().epochSecond
    
    // CSV file names
    private val nodesCSV = "nodes_${currentEpoch}.csv"
    private val waysCSV = "ways_${currentEpoch}.csv"
    private val relationsCSV = "relations_${currentEpoch}.csv"
    private val tagsCSV = "tags_${currentEpoch}.csv"
    
    // Track max changeset ID
    private var maxChangesetId = latestChangeset
    
    /**
     * Fetch XML data from a URL and return its content as a string
     */
    private fun fetchXml(url: String): String {
        val client = HttpClient.newBuilder().build()
        val request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .GET()
            .build()
            
        try {
            val response = client.send(request, HttpResponse.BodyHandlers.ofString())
            
            when (response.statusCode()) {
                429 -> {
                    println("Error: Too many requests to $url (status code 429)")
                    System.exit(1)
                }
                200 -> return response.body()
                else -> throw Exception("Failed to fetch $url (status code ${response.statusCode()})")
            }
        } catch (e: Exception) {
            throw Exception("Failed to fetch $url: ${e.message}")
        }
        
        return ""
    }
    
    /**
     * Parse only the create actions from the OSM XML diff.
     * Separates node, way, relation records and extracts tag rows.
     * For ways, builds a WKT geometry from <nd> children.
     * Returns four lists: nodes, ways, relations, tags.
     */
    private fun parseOsmCreate(xmlData: String): ParsedData {
        val nodes = mutableListOf<Map<String, Any?>>()
        val ways = mutableListOf<Map<String, Any?>>()
        val relations = mutableListOf<Map<String, Any?>>()
        val tags = mutableListOf<Map<String, Any?>>()
        
        val factory = DocumentBuilderFactory.newInstance()
        val builder = factory.newDocumentBuilder()
        val document = builder.parse(InputSource(StringReader(xmlData)))
        
        // Process each <action> element
        val actionElements = document.getElementsByTagName("action")
        for (i in 0 until actionElements.length) {
            val action = actionElements.item(i) as Element
            val actionType = action.getAttribute("type")
            
            if (actionType != "create") continue // Only process create actions
            
            // Find the created element (usually under <new>)
            val newElements = action.getElementsByTagName("new")
            val elem = if (newElements.length > 0) {
                val newElem = newElements.item(0) as Element
                if (newElem.childNodes.length > 0) {
                    findFirstElementChild(newElem)
                } else null
            } else {
                findFirstElementChild(action)
            } ?: continue
            
            // Convert timestamp to epoch milliseconds
            val timestamp = elem.getAttribute("timestamp")
            val epochMillis = if (timestamp.isNotEmpty()) {
                try {
                    val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")
                    val zonedDateTime = ZonedDateTime.parse(timestamp, formatter.withZone(ZoneId.of("UTC")))
                    zonedDateTime.toInstant().toEpochMilli()
                } catch (e: Exception) {
                    null
                }
            } else null
            
            val elemType = elem.nodeName
            val elemId = elem.getAttribute("id")
            
            // Update max changeset ID
            val changeset = elem.getAttribute("changeset").toLongOrNull() ?: 0L
            maxChangesetId = maxOf(maxChangesetId, changeset)
            
            // Extract tags for this element
            val tagElements = elem.getElementsByTagName("tag")
            for (j in 0 until tagElements.length) {
                val tag = tagElements.item(j) as Element
                val key = tag.getAttribute("k")
                val value = tag.getAttribute("v")
                
                tags.add(mapOf(
                    "epochMillis" to epochMillis,
                    "type" to elemType,
                    "id" to elemId,
                    "key" to key,
                    "value" to value
                ))
            }
            
            when (elemType) {
                "node" -> {
                    nodes.add(mapOf(
                        "epochMillis" to epochMillis,
                        "id" to elemId,
                        "version" to elem.getAttribute("version"),
                        "changeset" to elem.getAttribute("changeset"),
                        "username" to elem.getAttribute("user"),
                        "uid" to elem.getAttribute("uid"),
                        "lat" to elem.getAttribute("lat"),
                        "lon" to elem.getAttribute("lon")
                    ))
                }
                "way" -> {
                    // Build WKT geometry from <nd> children
                    val coords = mutableListOf<Pair<Double, Double>>()
                    val ndElements = elem.getElementsByTagName("nd")
                    
                    for (j in 0 until ndElements.length) {
                        val nd = ndElements.item(j) as Element
                        val lat = nd.getAttribute("lat")
                        val lon = nd.getAttribute("lon")
                        
                        if (lat.isNotEmpty() && lon.isNotEmpty()) {
                            try {
                                coords.add(Pair(lon.toDouble(), lat.toDouble()))
                            } catch (e: NumberFormatException) {
                                continue
                            }
                        }
                    }
                    
                    val wktGeom = if (coords.isNotEmpty()) {
                        // If the way is closed (>=4 points and first equals last), output as POLYGON
                        if (coords.size >= 4 && coords.first() == coords.last()) {
                            val coordStr = coords.joinToString(", ") { "${it.first} ${it.second}" }
                            "POLYGON(($coordStr))"
                        } else {
                            val coordStr = coords.joinToString(", ") { "${it.first} ${it.second}" }
                            "LINESTRING($coordStr)"
                        }
                    } else ""
                    
                    ways.add(mapOf(
                        "epochMillis" to epochMillis,
                        "id" to elemId,
                        "version" to elem.getAttribute("version"),
                        "changeset" to elem.getAttribute("changeset"),
                        "username" to elem.getAttribute("user"),
                        "uid" to elem.getAttribute("uid"),
                        "geometry" to wktGeom
                    ))
                }
                "relation" -> {
                    // For relations, output a comma-separated list of member refs as geometry
                    val members = elem.getElementsByTagName("member")
                    val memberRefs = mutableListOf<String>()
                    
                    for (j in 0 until members.length) {
                        val member = members.item(j) as Element
                        val ref = member.getAttribute("ref")
                        if (ref.isNotEmpty()) {
                            memberRefs.add(ref)
                        }
                    }
                    
                    val geometry = memberRefs.joinToString(",")
                    
                    relations.add(mapOf(
                        "epochMillis" to epochMillis,
                        "id" to elemId,
                        "version" to elem.getAttribute("version"),
                        "changeset" to elem.getAttribute("changeset"),
                        "username" to elem.getAttribute("user"),
                        "uid" to elem.getAttribute("uid"),
                        "geometry" to geometry
                    ))
                }
            }
        }
        
        return ParsedData(nodes, ways, relations, tags)
    }
    
    /**
     * Helper function to find the first Element child of a node
     */
    private fun findFirstElementChild(parent: Element): Element? {
        val children = parent.childNodes
        for (i in 0 until children.length) {
            val child = children.item(i)
            if (child is Element) {
                return child
            }
        }
        return null
    }
    
    /**
     * Write rows (a list of maps) to a CSV file and optionally print to stdout
     */
    private fun writeCsvDict(rows: List<Map<String, Any?>>, csvFile: String, fieldnames: List<String>) {
        // Write to actual file
        FileWriter(csvFile).use { writer ->
            // Write header
            writer.write(fieldnames.joinToString(",") + "\n")
            
            // Write rows
            for (row in rows) {
                val values = fieldnames.map { fieldname ->
                    val value = row[fieldname]
                    when (value) {
                        null -> ""
                        is String -> "\"${value.replace("\"", "'")}\"" 
                        else -> value.toString()
                    }
                }
                writer.write(values.joinToString(",") + "\n")
            }
        }
        
        // Print to stdout if verbose
        if (verbose) {
            println("\n--- $csvFile ---")
            File(csvFile).readText().let { println(it) }
        }
    }
    
    /**
     * Main function to fetch and process OSM minutely changes
     */
    fun process() {
        val url = "https://overpass-api.de/api/augmented_diff?id=$maxChangesetId"
        
        try {
            val xmlData = fetchXml(url)
            val (nodes, ways, relations, tags) = parseOsmCreate(xmlData)
            
            // Write nodes CSV
            if (verbose) {
                println("\n--- nodes.csv ---")
            }
            if (processNodes) {
                writeCsvDict(
                    nodes,
                    nodesCSV,
                    listOf("epochMillis", "id", "version", "changeset", "username", "uid", "lat", "lon")
                )
            }
            
            // Write ways CSV
            if (verbose) {
                println("\n--- ways.csv ---")
            }
            if (processWays) {
                writeCsvDict(
                    ways,
                    waysCSV,
                    listOf("epochMillis", "id", "version", "changeset", "username", "uid", "geometry")
                )
            }
            
            // Write relations CSV
            if (verbose) {
                println("\n--- relations.csv ---")
            }
            if (processRelations) {
                writeCsvDict(
                    relations,
                    relationsCSV,
                    listOf("epochMillis", "id", "version", "changeset", "username", "uid", "geometry")
                )
            }
            
            // Write tags CSV
            if (verbose) {
                println("\n--- tags.csv ---")
            }
            if (processTags) {
                writeCsvDict(
                    tags,
                    tagsCSV,
                    listOf("epochMillis", "type", "id", "key", "value")
                )
            }
            
            // Write new max changeset ID to file if path is provided
            if (etagPath != null) {
                File(etagPath).writeText(maxChangesetId.toString())
                if (verbose) {
                    println("\nWrote new max changeset ID $maxChangesetId to $etagPath")
                }
            }
            
        } catch (e: Exception) {
            println("Error: ${e.message}")
            System.exit(1)
        }
    }
    
    /**
     * Data class to hold the parsed data from the OSM XML diff
     */
    data class ParsedData(
        val nodes: List<Map<String, Any?>>,
        val ways: List<Map<String, Any?>>,
        val relations: List<Map<String, Any?>>,
        val tags: List<Map<String, Any?>>
    )
}

/**
 * Main function to run the OSM Minutely Consumer
 */
fun main() {
    OsmMinutelyConsumer().process()
}

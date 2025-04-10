import org.openstreetmap.osmosis.core.container.v0_6.EntityContainer
import org.openstreetmap.osmosis.core.domain.v0_6.Entity
import org.openstreetmap.osmosis.core.domain.v0_6.Node
import org.openstreetmap.osmosis.core.domain.v0_6.Relation
import org.openstreetmap.osmosis.core.domain.v0_6.Way
import org.openstreetmap.osmosis.core.task.v0_6.Sink
import org.openstreetmap.osmosis.pbf2.v0_6.PbfReader
import java.io.File
import java.io.FileWriter
import kotlin.io.path.Path
import kotlin.io.path.exists
import kotlin.math.max
import kotlin.math.min

class OsmToCsvConverter(private val inputFile: String, private val outputPath: String) {

    init {
        if (!inputFile.endsWith(".osm.pbf")) {
            throw IllegalArgumentException("Input file must be an OSM PBF file: $inputFile")
        }
        val inputPath = Path(inputFile)
        if (!inputPath.exists()) {
            if (!inputPath.parent.exists()) {
                throw IllegalArgumentException("Input file does not exist: $inputPath, and neither does its parent folder: ${inputPath.parent}")
            }
            throw IllegalArgumentException("Input file must exist: $inputPath")
        }
    }

    private val writeTags = !System.getenv("TAGS").isNullOrEmpty()
    private val writeNodes = !System.getenv("NODES").isNullOrEmpty()
    private val writeWays = !System.getenv("WAYS").isNullOrEmpty()
    private val writeRelations = !System.getenv("RELATIONS").isNullOrEmpty()
    private val writeMembers = !System.getenv("MEMBERS").isNullOrEmpty()

    private val base = inputFile.removeSuffix(".osm.pbf")
    private val tagWriter: FileWriter? = if (writeTags) FileWriter("${base}-tags.csv") else null
    private val nodeWriter: FileWriter? = if (writeNodes) FileWriter("${base}-nodes.csv") else null
    private val wayWriter: FileWriter? = if (writeWays) FileWriter("${base}-ways.csv") else null
    private val relationWriter: FileWriter? = if (writeRelations) FileWriter("${base}-relations.csv") else null
    private val membersWriter: FileWriter? = if (writeMembers) FileWriter("${base}-members.csv") else null

    var minLatitude = Double.MAX_VALUE
    var maxLatitude = Double.MIN_VALUE
    var minLongitude = Double.MAX_VALUE
    var maxLongitude = Double.MIN_VALUE
    var maxTimestamp = 0L

    init {
        println("Writing output to: $base-*.csv and $outputPath")
        tagWriter?.write("epochMillis,type,id,key,value\n")
        nodeWriter?.write("epochMillis,id,version,changeset,username,uid,lat,lon\n")
        wayWriter?.write("epochMillis,id,version,changeset,username,uid,geometry\n")
        relationWriter?.write("epochMillis,id,version,changeset,username,uid\n")
        membersWriter?.write("relationId,memberId,memberRole,memberType\n")
    }

    fun entityColumns(entity: Entity): String {
        return "${entity.timestamp.time},${entity.id},${entity.version},${entity.changesetId},${entity.user.name},${entity.user.id}"
    }

    fun convert() {
        val reader = PbfReader(File(inputFile), 4)
        val nodeToLatLon = HashMap<Long, LatLon>()

        reader.setSink(object : Sink {
            override fun process(entityContainer: EntityContainer) {
                val it = entityContainer.entity

                if (writeTags) {
                    for (tag in it.tags) {
                        val type = it.javaClass.simpleName.lowercase()
                        tagWriter?.write("${it.timestamp.time},${type},${it.id},\"${quote(tag.key)}\",\"${quote(tag.value)}\"\n")
                    }
                }

                maxTimestamp = max(maxTimestamp, it.timestamp.time)

                when (it) {
                    is Node -> {
                        if (writeNodes) {
                            nodeWriter?.write("${entityColumns(it)},${it.latitude},${it.longitude}\n")
                        }
                        val location = LatLon(it.latitude, it.longitude)
                        minLatitude = min(minLatitude, location.lat)
                        maxLatitude = max(maxLatitude, location.lat)
                        minLongitude = min(minLongitude, location.lon)
                        maxLongitude = max(maxLongitude, location.lon)
                        nodeToLatLon[it.id] = LatLon(it.latitude, it.longitude)
                    }

                    is Way -> {
                        if (writeWays) {
                            val geometry = Wkt.convertToWkt(it.wayNodes.stream().map { nodeToLatLon[it.nodeId]!! }.toList())
                            wayWriter?.write("${entityColumns(it)},\"${geometry}\"\n")
                        }
                    }

                    is Relation -> {
                        if (writeRelations) {
                            relationWriter?.write("${entityColumns(it)}\n")
                        }
                        if (writeMembers) {
                            for (member in it.members) {
                                membersWriter?.write("${it.id},${member.memberId},${member.memberRole},${member.memberType}\n")
                            }
                        }
                    }
                }
            }

            override fun initialize(map: Map<String, Any>) {
            }

            override fun complete() {
            }

            override fun close() {
            }
        })
        reader.run()
        writeBoundsToFile()
        writeMaxTimestampToFile()
    }

    private fun quote(value: String): String {
        return value.replace("\"", "'")
    }

    private fun writeMaxTimestampToFile() {
        val file = File(outputPath)
        file.writeText("-$maxTimestamp\n")
    }

    private fun writeBoundsToFile() {
        val boundsFile = File("${base}-bounds.txt")
        boundsFile.writeText("minLatitude=$minLatitude\nmaxLatitude=$maxLatitude\nminLongitude=$minLongitude\nmaxLongitude=$maxLongitude\n")
    }

    fun closeAllWriters() {
        try {
            tagWriter?.close()
            nodeWriter?.close()
            wayWriter?.close()
            relationWriter?.close()
            membersWriter?.close()
        } catch (e: Exception) {
            println("Error closing FileWriters: ${e.message}")
        }
    }
}

fun main(args: Array<String>) {
    if (args.size < 2) {
        println("Please provide the path to the OSM PBF file and the path to a file where the maximum timestamp should be written")
        return
    }

    val converter = OsmToCsvConverter(args[0], args[1])
    try {
        converter.convert()
    } finally {
        converter.closeAllWriters()
    }
}

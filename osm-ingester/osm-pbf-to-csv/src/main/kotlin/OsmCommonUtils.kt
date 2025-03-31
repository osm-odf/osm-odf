package osm.odf

import java.io.File
import java.io.FileWriter
import java.time.Instant
import java.time.ZoneId
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter

object OsmCommonUtils {
    /**
     * Common CSV writing functionality used by both converters
     */
    fun writeCsvDict(rows: List<Map<String, Any?>>, csvFile: String, fieldnames: List<String>, verbose: Boolean = false) {
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
        
        if (verbose) {
            println("\n--- $csvFile ---")
            File(csvFile).readText().let { println(it) }
        }
    }

    /**
     * Common timestamp parsing
     */
    fun parseOsmTimestamp(timestamp: String): Long? {
        return if (timestamp.isNotEmpty()) {
            try {
                val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")
                ZonedDateTime.parse(timestamp, formatter.withZone(ZoneId.of("UTC")))
                    .toInstant()
                    .toEpochMilli()
            } catch (e: Exception) {
                null
            }
        } else null
    }

    /**
     * Common string quoting for CSV
     */
    fun quoteCsvValue(value: String): String {
        return value.replace("\"", "'")
    }
}

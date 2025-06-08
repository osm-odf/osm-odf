import org.openstreetmap.osmosis.core.container.v0_6.EntityContainer
import org.openstreetmap.osmosis.core.domain.v0_6.Entity
import org.openstreetmap.osmosis.core.domain.v0_6.Node
import org.openstreetmap.osmosis.core.domain.v0_6.Relation
import org.openstreetmap.osmosis.core.domain.v0_6.Way
import org.openstreetmap.osmosis.core.task.v0_6.Sink
import org.openstreetmap.osmosis.pbf2.v0_6.PbfReader
import java.io.File
import java.time.Instant
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

    private fun enabled(envVar: String): Boolean = System.getenv(envVar) == "1"

    private val writeTags = enabled("TAGS")
    private val writeNodes = enabled("NODES")
    private val writeWays = enabled("WAYS")
    private val writeRelations = enabled("RELATIONS")
    private val writeMembers = enabled("MEMBERS")

    private val base = inputFile.removeSuffix(".osm.pbf")

    var minLatitude = Double.MAX_VALUE
    var maxLatitude = Double.MIN_VALUE
    var minLongitude = Double.MAX_VALUE
    var maxLongitude = Double.MIN_VALUE
    var maxTimestamp = 0L

    init {
        if (writeTags) println("epochMillis,type,id,key,value")
        if (writeNodes) println("epochMillis,id,version,changeset,username,uid,lat,lon")
        if (writeWays) println("epochMillis,id,version,changeset,username,uid,geometry")
        if (writeRelations) println("epochMillis,id,version,changeset,username,uid")
        if (writeMembers) println("relationId,memberId,memberRole,memberType")
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
                        println("${it.timestamp.time},${type},${it.id},\"${quote(tag.key)}\",\"${quote(tag.value)}\"")
                    }
                }

                if (it is Node || it is Way || it is Relation) {
                    maxTimestamp = max(maxTimestamp, it.timestamp.time)
                }

                when (it) {
                    is Node -> {
                        if (writeNodes) {
                            println("${entityColumns(it)},${it.latitude},${it.longitude}")
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
                            println("${entityColumns(it)},\"${geometry}\"")
                        }
                    }

                    is Relation -> {
                        if (writeRelations) {
                            println(entityColumns(it))
                        }
                        if (writeMembers) {
                            for (member in it.members) {
                                println("${it.id},${member.memberId},${member.memberRole},${member.memberType}")
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

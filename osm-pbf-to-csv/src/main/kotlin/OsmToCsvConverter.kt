import org.openstreetmap.osmosis.core.container.v0_6.EntityContainer
import org.openstreetmap.osmosis.core.domain.v0_6.Entity
import org.openstreetmap.osmosis.core.domain.v0_6.Node
import org.openstreetmap.osmosis.core.domain.v0_6.Relation
import org.openstreetmap.osmosis.core.domain.v0_6.Way
import org.openstreetmap.osmosis.core.task.v0_6.Sink
import org.openstreetmap.osmosis.pbf2.v0_6.PbfReader
import java.io.File
import java.io.FileWriter

class OsmToCsvConverter(private val inputFile: String)
{
    private val base = inputFile.removeSuffix(".osm.pbf")
    private val tagWriter = FileWriter("${base}-tags.csv")
    private val nodeWriter = FileWriter("${base}-nodes.csv")
    private val wayWriter = FileWriter("${base}-ways.csv")
    private val relationWriter = FileWriter("${base}-relations.csv")

    init
    {
        tagWriter.write("epochMillis,type,id,key,value\n")
        nodeWriter.write("epochMillis,id,version,changeset,username,uid,lat,lon\n")
        wayWriter.write("epochMillis,id,version,changeset,username,uid,geometry\n")
        relationWriter.write("epochMillis,id,version,changeset,username,uid,members\n")
    }

    fun entityColumns(entity: Entity): String
    {
        return "${entity.timestamp.time},${entity.id},${entity.version},${entity.changesetId},${entity.user.name},${entity.user.id}"
    }

    fun convert()
    {
        val reader = PbfReader(File(inputFile), 4)
        val nodeToLatLon = HashMap<Long, LatLon>()

        reader.setSink(object : Sink
        {
            override fun process(entityContainer: EntityContainer)
            {
                val it = entityContainer.entity

                for (tag in it.tags)
                {
                    val type = it.javaClass.simpleName.lowercase()
                    tagWriter.write("${it.timestamp.time},${type},${it.id},\"${quote(tag.key)}\",\"${quote(tag.value)}\"\n")
                }

                when (it)
                {
                    is Node ->
                    {
                        nodeWriter.write("${entityColumns(it)},${it.latitude},${it.longitude}\n")
                        nodeToLatLon[it.id] = LatLon(it.latitude, it.longitude)
                    }

                    is Way ->
                    {
                        val geometry = Wkt.convertToWkt(it.wayNodes.stream().map { nodeToLatLon[it.nodeId]!! }.toList())
                        wayWriter.write("${entityColumns(it)},\"${geometry}\"\n")
                    }

                    is Relation ->
                    {
                    }
                }
            }

            override fun initialize(map: Map<String, Any>)
            {
            }

            override fun complete()
            {
                tagWriter.close()
                nodeWriter.close()
                wayWriter.close()
                relationWriter.close()
            }

            override fun close()
            {
            }
        })
        reader.run()
    }

    private fun quote(value: String): String
    {
        return value.replace("\"", "'")
    }
}

fun main(args: Array<String>)
{
    if (args.isEmpty())
    {
        println("Please provide the path to the OSM PBF file as an argument")
        return
    }

    OsmToCsvConverter(args[0]).convert()
}
import org.openstreetmap.osmosis.core.container.v0_6.EntityContainer
import org.openstreetmap.osmosis.core.domain.v0_6.Node
import org.openstreetmap.osmosis.core.domain.v0_6.Way
import org.openstreetmap.osmosis.core.task.v0_6.Sink
import org.openstreetmap.osmosis.pbf2.v0_6.PbfReader
import java.io.File
import java.io.FileWriter

class OsmToCsvConverter(private val inputFile: String)
{
    private val tagWriter = FileWriter("tags.csv")
    private val nodeWriter = FileWriter("nodes.csv")
    private val wayWriter = FileWriter("ways.csv")

    init
    {
        tagWriter.write("epochMillis,id,key,value\n")
        nodeWriter.write("epochMillis,id,latitude,longitude\n")
        wayWriter.write("epochMillis,id,nodeId,latitude,longitude\n")
    }

    fun convert()
    {
        val reader = PbfReader(File(inputFile), 4)
        val latitudes = HashMap<Long, Double>();
        val longitudes = HashMap<Long, Double>();
        reader.setSink(object : Sink
        {
            override fun process(entityContainer: EntityContainer)
            {
                val it = entityContainer.entity;
                val timeAndId = "${it.timestamp.time},${it.id}"

                for (tag in it.tags)
                {
                    tagWriter.write("${timeAndId},\"${quote(tag.key)}\",\"${quote(tag.value)}\"\n")
                }

                when (it)
                {
                    is Node ->
                    {
                        nodeWriter.write("${timeAndId},${it.latitude},${it.longitude}\n")
                        latitudes[it.id] = it.latitude
                        longitudes[it.id] = it.longitude
                    }

                    is Way ->
                    {
                        for (node in it.wayNodes)
                        {
                            wayWriter.write("${timeAndId},${node.nodeId},${latitudes[node.nodeId]},${longitudes[node.nodeId]}\n")
                        }
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
            }

            override fun close()
            {
            }
        })
        reader.run()
    }

    private fun quote(value: String): String
    {
        return value.replace("\"", "\\\"");
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
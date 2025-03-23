class Wkt
{
    companion object
    {
        private fun toWktPoint(latLon: LatLon): String
        {
            return "POINT(${latLon.lon} ${latLon.lat})"
        }

        private fun toWktLineString(points: List<LatLon>): String
        {
            val coordinates = points.joinToString(", ") { "${it.lon} ${it.lat}" }
            return "LINESTRING($coordinates)"
        }

        private fun toWktPolygon(points: List<LatLon>): String
        {
            if (points.isEmpty()) return "POLYGON(())"
            val coordinates = points.joinToString(", ") { "${it.lon} ${it.lat}" }
            // Ensure the polygon is closed by repeating the first point at the end
            return "POLYGON(($coordinates, ${points.first().lon} ${points.first().lat}))"
        }

        fun convertToWkt(points: List<LatLon>): String
        {
            if (points.size < 2)
            {
                // If there's only one point, return a Point WKT
                return toWktPoint(points.first())
            }
            return if (points.first() == points.last())
            {
                // If the first and last points are the same, it's a Polygon
                toWktPolygon(points)
            }
            else
            {
                // Otherwise, it's a LineString
                toWktLineString(points)
            }
        }
    }
}
# Build and run kotlin program
# Environment variable for PBF file
# Use official Gradle image for building
FROM gradle:8.10-jdk17 AS build

# Set working directory
WORKDIR /app

# Copy build files first to leverage Docker cache
COPY build.gradle.kts .
COPY settings.gradle.kts .
COPY gradle.properties .
COPY gradlew .
COPY gradlew.bat .
COPY gradle ./gradle

# Copy source code
COPY src ./src

# Build the project
RUN ./gradlew build

# Use slim JDK image for runtime
FROM eclipse-temurin:17-jre-jammy

# Set working directory
WORKDIR /app

# Copy built artifacts from build stage
COPY --from=build /app/build/libs/*.jar ./app.jar

# Create directory for input files
RUN mkdir /input

# Set working directory for input files
WORKDIR /input

# Set entrypoint with default argument
CMD ["java", "-jar", "/app/app.jar", "/input/berlin/berlin-latest-internal.osm.pbf"]

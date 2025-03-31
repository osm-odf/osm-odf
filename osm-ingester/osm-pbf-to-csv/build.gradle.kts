plugins {
    kotlin("jvm") version "2.0.21"
    java
    application
}

kotlin {
    jvmToolchain(17)
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}

group = "osm-odf"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(kotlin("test"))
    implementation("org.openstreetmap.osmosis:osmosis-pbf2:0.49.2")
    implementation("org.openstreetmap.osmosis:osmosis-core:0.48.3")
}

tasks.test {
    useJUnitPlatform()
}

tasks.jar {
    manifest {
        attributes["Main-Class"] = "OsmToCsvConverterKt"
    }
    from(configurations.runtimeClasspath.get().map { if (it.isDirectory) it else zipTree(it) })
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
}

// Create a task for the OsmMinutelyConsumer
task("runConsumer", JavaExec::class) {
    group = "application"
    description = "Run the OsmMinutelyConsumer"
    mainClass.set("OsmMinutelyConsumerKt")
    classpath = sourceSets["main"].runtimeClasspath
}

// Create a fat JAR for the consumer
tasks.register<Jar>("consumerJar") {
    group = "build"
    description = "Assembles a fat JAR for the OsmMinutelyConsumer"
    archiveBaseName.set("osm-minutely-consumer")
    manifest {
        attributes["Main-Class"] = "OsmMinutelyConsumerKt"
    }
    from(configurations.runtimeClasspath.get().map { if (it.isDirectory) it else zipTree(it) })
    with(tasks.jar.get())
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
}

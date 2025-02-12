plugins {
    kotlin("jvm") version "2.0.21"
    java
}

kotlin {
    jvmToolchain(21)
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

group = "com.github.jonathanlocke.osm.osm-to-csv"
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
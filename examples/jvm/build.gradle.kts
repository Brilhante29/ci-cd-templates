plugins {
    base
}

tasks.register("verifyFixture") {
    group = "verification"
    doLast {
        check(file("fixture.txt").readText().trim() == "verified")
    }
}

tasks.named("check") {
    dependsOn("verifyFixture")
}

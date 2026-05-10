FROM maven:3.9.9-eclipse-temurin-17 AS build

WORKDIR /build
COPY services/java-gateway/pom.xml pom.xml
COPY services/java-gateway/src src

RUN mvn -q -DskipTests package

FROM eclipse-temurin:17-jre

WORKDIR /app
COPY --from=build /build/target/java-gateway-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "/app/app.jar"]

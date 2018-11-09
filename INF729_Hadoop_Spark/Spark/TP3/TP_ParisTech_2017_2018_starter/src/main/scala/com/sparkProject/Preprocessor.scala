package com.sparkProject

import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql

object Preprocessor {

  def main(args: Array[String]): Unit = {

    // Des réglages optionels du job spark. Les réglages par défaut fonctionnent très bien pour ce TP
    // on vous donne un exemple de setting quand même
    val conf = new SparkConf().setAll(Map(
      "spark.scheduler.mode" -> "FIFO",
      "spark.speculation" -> "false",
      "spark.reducer.maxSizeInFlight" -> "48m",
      "spark.serializer" -> "org.apache.spark.serializer.KryoSerializer",
      "spark.kryoserializer.buffer.max" -> "1g",
      "spark.shuffle.file.buffer" -> "32k",
      "spark.default.parallelism" -> "12",
      "spark.sql.shuffle.partitions" -> "12"
    ))

    // Initialisation de la SparkSession qui est le point d'entrée vers Spark SQL (donne accès aux dataframes, aux RDD,
    // création de tables temporaires, etc et donc aux mécanismes de distribution des calculs.)
    val spark = SparkSession
      .builder
      .config(conf)
      .appName("TP_spark")
      .getOrCreate()


    /*******************************************************************************
      *
      *       TP 2
      *
      *       - Charger un fichier csv dans un dataFrame
      *       - Pre-processing: cleaning, filters, feature engineering => filter, select, drop, na.fill, join, udf, distinct, count, describe, collect
      *       - Sauver le dataframe au format parquet
      *
      *       if problems with unimported modules => sbt plugins update
      *
      ********************************************************************************/

    //println("hello world ! from Preprocessor")

    //val path = "/cal/homes/soufflet/Downloads/train.csv"
    //val file = csv(path)
    val df = spark.read.format("csv")
      .option("header", "true")
      .option("inferSchema", "true")
      .load("/cal/homes/soufflet/Downloads/train_clean.csv")

    //df.show(10) //ok
    //print(df.col())
    //println(df.describe())
    println(df.count()) //ok
    //println(df.schema.fields.count())
    df.schema.fields.foreach(x => println(x)) //ok



    val df_1 = df.withColumn(colName = "goal", df("goal").cast("Int"))
      .withColumn("deadline",df("deadline").cast("Int"))
      .withColumn("state_changed_at",df("state_changed_at").cast("Int"))
      .withColumn("created_at",df("created_at").cast("Int"))
      .withColumn("launched_at", df("launched_at").cast("Int"))
    // OK
    //df_1.schema.fields.foreach(x => println(x))

    // 2/ Cleaning
    // a
    // OK but check what the interesting columns
    df_1.describe("goal","deadline","state_changed_at","created_at","launched_at","backers_count","final_status").show()

    // b data observation.
    // categorical data : country, currency, final status
    // not useful columns : disable_communication?
    df_1.show()


  }

}

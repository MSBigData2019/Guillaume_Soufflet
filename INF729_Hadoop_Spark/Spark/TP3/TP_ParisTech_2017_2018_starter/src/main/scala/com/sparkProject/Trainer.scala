package com.sparkProject

import org.apache.spark.SparkConf
import org.apache.spark.ml.evaluation.MulticlassClassificationEvaluator
import org.apache.spark.sql.SparkSession
import org.apache.spark.ml.feature.{RegexTokenizer, IDF, StopWordsRemover, CountVectorizer, CountVectorizerModel}
import org.apache.spark.ml.feature.{StringIndexer, OneHotEncoder}
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.ml.feature.VectorAssembler
import org.apache.spark.ml.{Pipeline, PipelineModel}
import org.apache.spark.ml.classification.{BinaryLogisticRegressionSummary, LogisticRegression}
import org.apache.spark.ml.tuning.{TrainValidationSplit, ParamGridBuilder}
import org.apache.spark.mllib.evaluation.BinaryClassificationMetrics



object Trainer {

  def main(args: Array[String]): Unit = {

    val conf = new SparkConf().setAll(Map(
      "spark.scheduler.mode" -> "FIFO",
      "spark.speculation" -> "false",
      "spark.reducer.maxSizeInFlight" -> "48m",
      "spark.serializer" -> "org.apache.spark.serializer.KryoSerializer",
      "spark.kryoserializer.buffer.max" -> "1g",
      "spark.shuffle.file.buffer" -> "32k",
      "spark.default.parallelism" -> "12",
      "spark.sql.shuffle.partitions" -> "12",
      "spark.driver.maxResultSize" -> "2g"
    ))

    val spark = SparkSession
      .builder
      .config(conf)
      .appName("TP_spark")
      .getOrCreate()


    /*******************************************************************************
      *
      *       TP 3
      *
      *       - lire le fichier sauvegarder précédemment
      *       - construire les Stages du pipeline, puis les assembler
      *       - trouver les meilleurs hyperparamètres pour l'entraînement du pipeline avec une grid-search
      *       - Sauvegarder le pipeline entraîné
      *
      *       if problems with unimported modules => sbt plugins update
      *
      ********************************************************************************/


    /***** Lecture du dataset ******/
    val df = spark.read.parquet("/cal/homes/soufflet/INF_729/TP_spark_final/prepared_trainingset")
/**    df.printSchema()
  * df.show(5)
**/
    /***** Stage 1: Tokenisation de la colonne "text"  ******/
    val tokenizer = new RegexTokenizer()
      .setPattern("\\W+")
      .setGaps(true)
      .setInputCol("text")
      .setOutputCol("tokens")

    /***** Stage 2: Retirer les stop words  ******/
    StopWordsRemover.loadDefaultStopWords("english")

    val remover = new StopWordsRemover()
      .setInputCol("tokens")
      .setOutputCol("filtered")

    /***** Stage 3: Appliquer TF de l'algorithme TF-IDF en utilisant CountVectorizer ******/
    val cv = new CountVectorizer()
      .setInputCol("filtered")
      .setOutputCol("rawFeatures")
      .setMinTF(2) // minTF: occurence min au sein d'un doc
//      .setMinDF(2) // minDF : occurence min entre les doc

    /***** Stage 4: Appliquer IDF de l'algorithme TF-IDF  ******/
    val idf = new IDF()
      .setInputCol("rawFeatures")
      .setOutputCol("tfidf")

    /***** Stage 5: Convertir “country2” en quantités numériques dans "country_indexed" ******/

    val indexerCountry = new StringIndexer()
      .setInputCol("country2")
      .setOutputCol("country_indexed")

    /***** Stage 6: Convertir “currency2” en quantités numériques dans "currency_indexed" ******/

    val indexerCurrency = new StringIndexer()
      .setInputCol("currency2")
      .setOutputCol("currency_indexed")

    /***** Stages 7&8: Convertir en one hot encoders ******/
    val encoderCountry = new OneHotEncoder()
      .setInputCol("country_indexed")
      .setOutputCol("country_onehot")

    val encoderCurrency = new OneHotEncoder()
      .setInputCol("currency_indexed")
      .setOutputCol("currency_onehot")

    /***** Stage 9: Assembler les features "tfidf", "days_campaign", "hours_prepa", "goal", "country_onehot", "currency_onehot"  dans une seule colonne “features” ******/
    val assembler = new VectorAssembler()
      .setInputCols(Array("tfidf", "days_campaign", "hours_prepa", "goal", "country_onehot", "currency_onehot"))
      .setOutputCol("features")

    /***** Stage 10: Définir le modèle classification ******/
    val lr = new LogisticRegression()
      .setElasticNetParam(0.0)
      .setFitIntercept(true)
      .setFeaturesCol("features")
      .setLabelCol("final_status")
      .setStandardization(true)
      .setPredictionCol("predictions")
      .setRawPredictionCol("raw_predictions")
      .setThresholds(Array(0.7, 0.3))
      .setTol(1.0e-6)
      .setMaxIter(300)

    /***** Stage 11: Définir le pipeline assemblant les stages 1 à 10 ******/
    val pipeline = new Pipeline()
      .setStages(Array(tokenizer, remover, cv, idf, indexerCountry, indexerCurrency, encoderCountry, encoderCurrency, assembler, lr))

    /***** Stage 12: Définir un training set et un test set ******/
    val Array(training, test) = df.randomSplit(Array[Double](0.9, 0.1), seed=18L)
    training.cache()

    /***** Stage 13: Définir la grid-search ******/
    val minDFs = Array(55.0, 75.0, 95.0)
    val lr_regParams = Array(1e-8, 1e-6, 1e-4, 1e-2)

    val gridSearch = new ParamGridBuilder()
      .addGrid(lr.regParam, lr_regParams)
      .addGrid(cv.minDF, minDFs)
      .build()

    /******* Définir l'estimateur du modèle ***********/
    val f1Estimator = new MulticlassClassificationEvaluator()
      .setMetricName("f1")
      .setLabelCol("final_status")
      .setPredictionCol("predictions")

    /***** Entrainer le modèle sur la grid-search ******/
    val trainValidationSplit = new TrainValidationSplit()
      .setEstimator(pipeline)
      .setEvaluator(f1Estimator)
      .setEstimatorParamMaps(gridSearch)
      .setTrainRatio(0.7)

    val model = trainValidationSplit.fit(training)

    /***** Evaluer le modèle sur le jeu de test et afficher le F1 score*******/
    val df_WithPredictions = model
      .transform(test)
      .select("features", "final_status", "predictions", "raw_predictions")

    val f1Score = f1Estimator.evaluate(df_WithPredictions)

    println("F1 score : "+f1Score)

    df_WithPredictions.groupBy("final_status", "predictions").count.show()

    /******* Sauvegarder le modèle ********/
    model.save("INF729_TP_Spark_final_model")

  }
}

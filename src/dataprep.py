"""Preparação de dados do projeto: ingestão preguiçosa + transformação + imputação KNN.

Reúne as MESMAS funções usadas no notebook `notebooks/00_final.ipynb`, num módulo
reutilizável. Serve para aplicar o pipeline a dados novos (ex.: o notebook de inferência
`notebooks/07_inferencia_validacao.ipynb`) sem reescrever a lógica.

Decisões de projeto (idênticas ao 00_final):
- Ingestão por streaming (ijson) agregando os medicamentos por registro -> Parquet.
- Transformação como uma única query Polars preguiçosa (limpeza, faixa etária, features),
  materializada de uma vez em streaming. Atributos numéricos saem CRUS (sem padronizar):
  a padronização vive dentro do pipeline do modelo.
- Imputação da faixa etária por um classificador KNN ajustado SOMENTE no treino.

Convenções: código em inglês, comentários em pt-BR.
"""
from __future__ import annotations

from pathlib import Path

import ijson
import numpy as np
import polars as pl
import pyarrow.parquet as pq
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "serious"

# Atributos preditores do imputador KNN da faixa etária.
KNN_FEATURES = [
    "occurcountry", "patient.patientsex", "patient.drug.drugcharacterization",
    "patient.drug.activesubstance.activesubstancename",
    "patient.drug.medicinalproduct", "patient.drug.count",
]

# Códigos de unidade de idade do OpenFDA -> fator de conversão para anos.
AGE_UNIT_TO_YEARS = {
    "800": 10.0,        # década
    "801": 1.0,         # ano
    "802": 1 / 12,      # mês
    "803": 1 / 52,      # semana
    "804": 1 / 365,     # dia
    "805": 1 / (365 * 24),  # hora
}

# Schema fixo do Parquet bruto: tipos estáveis entre lotes e arquivos.
RAW_SCHEMA = {
    "safetyreportid": pl.Utf8,
    "serious": pl.Utf8,
    "occurcountry": pl.Utf8,
    "patient.patientsex": pl.Utf8,
    "patient.patientonsetage": pl.Float64,
    "patient.patientonsetageunit": pl.Utf8,
    "patient.drug.activesubstance.activesubstancename": pl.Utf8,
    "patient.drug.drugcharacterization": pl.Utf8,
    "patient.drug.medicinalproduct": pl.Utf8,
    "patient.drug.count": pl.Int64,
}


# --------------------------------------------------------------------------- ingestão
def normalize_text_value(value):
    """Normaliza texto para MAIÚSCULAS sem espaços nas bordas; None se vazio/ausente."""
    if value is None:
        return None
    value = str(value).strip()
    return value.upper() if value else None


def join_unique_values(values):
    """Resume várias entradas em texto único e ordenado ('a | b'); 'unknown' se vazio."""
    vals = [str(v).strip() for v in values if v is not None and str(v).strip()]
    uniq = sorted(set(vals))
    return " | ".join(uniq) if uniq else "unknown"


def _to_float(value):
    """Converte para float; None quando não numérico (mantém o schema estável)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def flatten_report(rec):
    """Achata um relatório OpenFDA em uma linha, agregando sua lista patient.drug[].

    A agregação é feita por registro (memória O(1)), pois cada relatório já carrega seus
    próprios medicamentos.
    """
    patient = rec.get("patient") or {}
    drugs = patient.get("drug") or []
    if isinstance(drugs, dict):  # um único medicamento pode vir como objeto, não lista
        drugs = [drugs]
    active = join_unique_values(
        normalize_text_value((d.get("activesubstance") or {}).get("activesubstancename"))
        for d in drugs
    )
    medic = join_unique_values(
        normalize_text_value(d.get("medicinalproduct")) for d in drugs
    )
    drugchar = join_unique_values(
        None if d.get("drugcharacterization") is None
        else str(d.get("drugcharacterization")).strip()
        for d in drugs
    )
    sid = rec.get("safetyreportid")
    return {
        "safetyreportid": str(sid) if sid is not None else None,
        "serious": None if rec.get("serious") is None else str(rec.get("serious")),
        "occurcountry": rec.get("occurcountry"),
        "patient.patientsex": None if patient.get("patientsex") is None
        else str(patient.get("patientsex")),
        "patient.patientonsetage": _to_float(patient.get("patientonsetage")),
        "patient.patientonsetageunit": None if patient.get("patientonsetageunit") is None
        else str(patient.get("patientonsetageunit")),
        "patient.drug.activesubstance.activesubstancename": active,
        "patient.drug.drugcharacterization": drugchar,
        "patient.drug.medicinalproduct": medic,
        "patient.drug.count": len(drugs),
    }


def ingest_to_parquet(json_paths, dest_parquet, batch_size=20_000, max_records=None):
    """Lê os JSON em streaming e grava as linhas achatadas em Parquet, em lotes.

    `max_records` limita o total lido (útil para um teste rápido). Retorna o nº gravado.
    """
    dest_parquet = Path(dest_parquet)
    writer = None
    batch, total = [], 0

    def _flush(rows):
        nonlocal writer, total
        if not rows:
            return
        table = pl.DataFrame(rows, schema=RAW_SCHEMA).to_arrow()
        if writer is None:
            writer = pq.ParquetWriter(dest_parquet, table.schema)
        writer.write_table(table)
        total += len(rows)

    try:
        for path in json_paths:
            with open(path, "rb") as fh:
                for rec in ijson.items(fh, "results.item"):
                    batch.append(flatten_report(rec))
                    if len(batch) >= batch_size:
                        _flush(batch)
                        batch = []
                    if max_records is not None and total + len(batch) >= max_records:
                        break
            if max_records is not None and total + len(batch) >= max_records:
                break
        _flush(batch)
    finally:
        if writer is not None:
            writer.close()
    return total


# ----------------------------------------------------------------------- transformação
def _count_pipe(column):
    """Conta itens separados por '|' numa coluna de texto (0 quando 'unknown')."""
    col = pl.col(column)
    nonempty = col.str.split("|").list.eval(
        pl.element().str.strip_chars().str.len_chars() > 0
    ).list.sum()
    return (
        pl.when(col.str.to_lowercase() == "unknown").then(0).otherwise(nonempty)
    ).cast(pl.Int64)


def build_feature_frame(parquet_path):
    """Query Polars preguiçosa de limpeza + faixa etária + feature engineering.

    Igual ao 00_final, porém SEM filtrar por `serious` (para permitir inferência em dados
    sem rótulo). Numéricas saem cruas. Retorna um LazyFrame; a faixa etária ainda pode
    conter 'unknown' (preenchida depois pelo imputador KNN).
    """
    sex_map = {"1": "male", "2": "female", "0": "unknown"}

    age_years = (
        pl.col("patient.patientonsetage")
        * pl.col("patient.patientonsetageunit").replace_strict(
            AGE_UNIT_TO_YEARS, default=None
        )
    )
    age_years = (
        pl.when((age_years >= 0) & (age_years <= 120)).then(age_years).otherwise(None)
    )

    return (
        pl.scan_parquet(parquet_path)
        .filter(pl.col("occurcountry").is_not_null())  # relatório sem país é descartado
        .with_columns(
            pl.col("patient.patientsex")
            .replace_strict(sex_map, default="unknown")
            .alias("patient.patientsex"),
            age_years.alias("_age_years"),
        )
        .with_columns(
            pl.when(pl.col("_age_years").is_null()).then(pl.lit("unknown"))
            .when(pl.col("_age_years") < 2).then(pl.lit("baby_early_childhood"))
            .when(pl.col("_age_years") < 12).then(pl.lit("child"))
            .when(pl.col("_age_years") < 18).then(pl.lit("adolescent"))
            .when(pl.col("_age_years") < 30).then(pl.lit("young_adult"))
            .when(pl.col("_age_years") < 60).then(pl.lit("adult"))
            .otherwise(pl.lit("elderly"))
            .alias("patient.ageGroupCalculated")
        )
        .with_columns(
            (pl.col("patient.ageGroupCalculated") == "unknown")
            .cast(pl.Int64)
            .alias("patient.ageGroupCalculated_was_imputed"),
            _count_pipe("patient.drug.activesubstance.activesubstancename")
            .alias("feature_n_active_substances"),
            _count_pipe("patient.drug.drugcharacterization").alias("feature_n_drug_types"),
            (pl.col("patient.drug.medicinalproduct").str.to_lowercase() != "unknown")
            .cast(pl.Int64)
            .alias("feature_has_medicinal_product"),
            (pl.col("patient.drug.count") > 1).cast(pl.Int64).alias("feature_multiple_drugs"),
            (pl.col("occurcountry").str.to_uppercase() == "US")
            .cast(pl.Int64)
            .alias("feature_is_usa"),
            pl.col("serious").cast(pl.Int64, strict=False).alias("serious"),
        )
        .drop("_age_years", "patient.patientonsetage", "patient.patientonsetageunit")
    )


def materialize(parquet_path):
    """Materializa a query preguiçosa em DataFrame pandas (streaming, memória limitada)."""
    return build_feature_frame(parquet_path).collect(engine="streaming").to_pandas()


def prepare_dataframe(json_paths, parquet_path, max_records=None):
    """Atalho: ingere os JSON e devolve o DataFrame transformado (sem imputar idade)."""
    ingest_to_parquet(json_paths, parquet_path, max_records=max_records)
    return materialize(parquet_path)


# ----------------------------------------------------------- imputação KNN da faixa etária
def build_age_group_imputer():
    """Cria o imputador KNN da faixa etária (ColumnTransformer + KNeighborsClassifier).

    Categóricas via One-Hot, textos de medicamentos via CountVectorizer e a contagem
    padronizada; KNN k=5 ponderado por distância. Deve ser ajustado SÓ no treino.
    """
    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"),
         ["occurcountry", "patient.patientsex", "patient.drug.drugcharacterization"]),
        ("active_substance",
         CountVectorizer(max_features=100, token_pattern=r"(?u)\b[\w-]+\b"),
         "patient.drug.activesubstance.activesubstancename"),
        ("medicinal_product",
         CountVectorizer(max_features=100, token_pattern=r"(?u)\b[\w-]+\b"),
         "patient.drug.medicinalproduct"),
        ("num", StandardScaler(), ["patient.drug.count"]),
    ])
    return Pipeline([
        ("preprocessor", preprocessor),
        ("knn", KNeighborsClassifier(n_neighbors=5, weights="distance",
                                     algorithm="brute", metric="euclidean")),
    ])


def fit_age_group_imputer(train_df):
    """Ajusta o imputador KNN nos registros de treino com faixa etária conhecida."""
    imputer = build_age_group_imputer()
    known = train_df["patient.ageGroupCalculated"] != "unknown"
    imputer.fit(
        train_df.loc[known, KNN_FEATURES],
        train_df.loc[known, "patient.ageGroupCalculated"],
    )
    return imputer


def impute_age_groups(df, fitted_imputer):
    """Preenche as faixas 'unknown' de df com o imputador já ajustado (sem refit)."""
    df = df.copy()
    unknown = df["patient.ageGroupCalculated"] == "unknown"
    if unknown.any():
        df.loc[unknown, "patient.ageGroupCalculated"] = fitted_imputer.predict(
            df.loc[unknown, KNN_FEATURES]
        )
    return df

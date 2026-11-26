# Full-Cohort Evaluation Inventory

## Manuscript runs under judge protocol v5

The earlier inventory selected projected summary files with a question count of 2,000 and a quality-metrics object. The older evaluations have case verdicts even when that object is absent. The previous supplement flag governed additional numerical extraction; the archived JSONL verdicts were already public under artifact IDs. A version mention may denote a comparator or schema revision. The executing version in each row below was matched to the archived run settings.

| Executing version | Archived under | Cases | Strict | Partial | Strict or partial | E2E pass | Judge errors | Uncertain | Released case records | Original paginated projection |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| v1222 | v1222 | 2,000 | 1,513 | 328 | 1,841 | 1,512 | 0 | 0 | [Download](version-recovery/v1222.jsonl.gz) | [df2346c5d13b](review/artifacts/df/df2346c5d13bc94c98de369901521a517532dfcd1a0651248f0a74222d93da3c/README.md) |
| v1225 | v1225 | 2,000 | 1,590 | 253 | 1,843 | 1,589 | 1 | 0 | [Download](version-recovery/v1225.jsonl.gz) | [e2701d154f4f](review/artifacts/e2/e2701d154f4f55809b19d5056283d9c210c0bf9fe2ba090a16208c16514ff7a3/README.md) |
| v1226 | v1226 | 2,000 | 1,517 | 349 | 1,866 | 1,516 | 0 | 0 | [Download](version-recovery/v1226.jsonl.gz) | [6346324b5a1f](review/artifacts/63/6346324b5a1fc21d8fa89a0d7e82cd885e66da2283da11bec5dfdb7f63da96d8/README.md) |
| v1227 | v1227 | 2,000 | 1,542 | 279 | 1,821 | 1,540 | 1 | 0 | [Download](version-recovery/v1227.jsonl.gz) | [67b3baac8a46](review/artifacts/67/67b3baac8a46a29c9cc20a27cb88f96c62b795a0376a6c03ee4a2b1223ff6ab8/README.md) |
| v1371 | v1408 | 2,000 | 1,550 | 315 | 1,865 | 1,538 | 2 | 3 | [Download](version-recovery/v1371.jsonl.gz) | [ea2e69deceb2](review/artifacts/ea/ea2e69deceb2669f3fc046adce6f1caf95f2e76d58de03193a4524b50d719e13/README.md) |

Strict counts correct answers plus correct refusals. Errors and uncertain judgments remain in the denominator. For v1225 the 1,589 end-to-end passes and 1,590 strictly correct labels measure different outcomes. See the [run settings](audit-feedback/run-settings.json) and the [all-version recovery index](version-recovery/README.md).

The conventional control (1,318 strictly correct) and v1660 (1,451 strictly correct) use judge protocol v6. See the [control case labels](baseline-system-evaluation/case-labels.json) and [v1660 case labels](proposed-system-evaluation/case-labels.json). The case-level v1222 labels give 1,513 strict; the separately indexed 1,512-count summary below is retained as its own artifact.

[All archived streams with 2,000 rows](FULL_LENGTH_CASE_STREAMS.md)

## Historical summary candidates

These rows describe individual summary artifacts, including intermediate and rejected results. Match provenance before comparing or combining counts.

| Referenced versions | Artifact | Semantic correct / total | E2E pass | Judge errors | Judge uncertain |
|---|---|---|---|---|---|
| v1526 | [dea946aee4dc](summaries/dea946aee4dc4d0d519c10c6580bf81e41e331baeb6ea0a9d196161ead31f2c5.json) | 1210/2000 | 1197 | unreported | unreported |
| v1602 | [66c553f6ae63](summaries/66c553f6ae63a7614e071adea5474d034078861c63753c9e6f6100f5205e6520.json) | 1431/2000 | 1408 | 4 | 0 |
| v1660 | [cb3bbca7c4ab](summaries/cb3bbca7c4ab1aca5a7b2175d7237e3654b990ee5aad0ecad8e7749d852fd10d.json) | 1451/2000 | 1422 | 0 | 0 |
| v1660 | [eb4cad3a0942](summaries/eb4cad3a0942d6681406f35b7e7e5d92910bf36827ee457071266ebc6460f384.json) | 1450/2000 | 1421 | 0 | 1 |
| v1660 | [d2ca7b582a62](summaries/d2ca7b582a620a61d9f1eaa6c959b89c6aa94196973de0b003812ca0580304a7.json) | 1447/2000 | 1418 | 3 | 5 |
| v1222 | [07308c098482](summaries/07308c0984821cbd57ff9fd1ebe627edf308c148736ac65444cbf64e66ba5f48.json) | 1512/2000 | 1512 | unreported | unreported |
| v1441 | [427ca5b115dc](summaries/427ca5b115dc233f5d475aa896ec55648326b6fce6af15269f672b6784ca97f7.json) | 1435/2000 | 932 | unreported | unreported |
| v1441 | [602a7cf60c9f](summaries/602a7cf60c9f389ee04256d16c523461aa4269725803dd42490f90cceac61b11.json) | 1435/2000 | 1412 | 0 | 0 |
| v241 | [0fdb94cfb174](summaries/0fdb94cfb1746bc78197eb6a04d8249f121c2c2dae76bde37219475f1574fdb9.json) | 1117/2000 | 760 | unreported | unreported |
| v392 | [c968ae8d45ec](summaries/c968ae8d45ec5b92dc3def3a786af341fb2a0ff3af969b033d9052c2f1a85671.json) | 1306/2000 | 843 | unreported | unreported |
| v392 | [98a0dba230b1](summaries/98a0dba230b1b57fb40baa885aeb8b9e03c806592234e7cbcb11b494c5fa4d34.json) | 1414/2000 | 923 | unreported | unreported |
| v394 | [b6c60cc9d55a](summaries/b6c60cc9d55ad3828340b8064aa3a8145268b33be827d7eb3a90c229d4e367cd.json) | 1639/2000 | 1023 | unreported | unreported |

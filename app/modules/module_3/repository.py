from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Iterable, Any, Tuple

from app.modules.module_3.base import LabTest, TestStatus, ResultStatus
from app.modules.module_3.subclasses import BloodTest, ImagingTest, BiopsyTest, ReferenceRange, NumericResult

"""Ana Repositoryy"""
class InMemoryLabTestRepository:

    def __init__(self) -> None:
        self._tests: Dict[int, LabTest] = {}
        self._index_patient: Dict[int, set[int]] = {}
        self._index_type: Dict[str, set[int]] = {}
        self._history: list[dict] = []


    def add(self, test: LabTest) -> bool:
        if test.test_id in self._tests:
            return False
        self._tests[test.test_id] = test
        self._index_add(test)
        self._log("ADD", test.test_id)
        return True

    def update(self, test: LabTest) -> bool:
        if test.test_id not in self._tests:
            return False
        old = self._tests[test.test_id]
        self._index_remove(old)
        self._tests[test.test_id] = test
        self._index_add(test)
        self._log("UPDATE", test.test_id)
        return True

    def delete(self, test_id: int) -> bool:
        if test_id not in self._tests:
            return False
        test = self._tests.pop(test_id)
        self._index_remove(test)
        self._log("DELETE", test_id)
        return True

    def get(self, test_id: int) -> Optional[LabTest]:
        return self._tests.get(test_id)

    def list_all(self) -> List[LabTest]:
        return list(self._tests.values())

    def find_by_patient(self, patient_id: int) -> List[LabTest]:
        ids = self._index_patient.get(int(patient_id), set())
        return [self._tests[i] for i in ids if i in self._tests]

    def filter_by_type(self, test_type: str) -> List[LabTest]:
        key = test_type.strip()
        ids = self._index_type.get(key, set())
        return [self._tests[i] for i in ids if i in self._tests]

    def filter_by_status(self, status: TestStatus) -> List[LabTest]:
        return [t for t in self._tests.values() if t.status == status]

    def critical_results(self) -> List[LabTest]:
        return [t for t in self._tests.values() if t.result_status == ResultStatus.CRITICAL]

    def history(self, limit: int = 10) -> List[dict]:
        return self._history[-limit:]

    def clear(self) -> None:
        self._tests.clear()
        self._index_patient.clear()
        self._index_type.clear()
        self._history.clear()

    def _index_add(self, test: LabTest) -> None:
        self._index_patient.setdefault(test.patient_id, set()).add(test.test_id)
        self._index_type.setdefault(test.test_type, set()).add(test.test_id)

    def _index_remove(self, test: LabTest) -> None:
        self._index_patient.get(test.patient_id, set()).discard(test.test_id)
        self._index_type.get(test.test_type, set()).discard(test.test_id)

    def _log(self, action: str, test_id: int) -> None:
        self._history.append(
            {"time": datetime.now().isoformat(), "action": action, "test_id": test_id}
        )

    @staticmethod
    def new_repo() -> "InMemoryLabTestRepository":
        return InMemoryLabTestRepository()

    """veri ile repo oluştruma"""
    @classmethod
    def with_sample_data(cls) -> "InMemoryLabTestRepository":

        repo = cls()
        repo._history.append({"time": datetime.now().isoformat(), "action": "BOOT", "test_id": 0})
        return repo

"""Json dosyası"""
class JsonFileLabTestRepository:

    def __init__(self, file_path: str = "lab_tests.json") -> None:
        self._file_path = file_path
        self._raw: Dict[str, dict] = {}
        self._load()

    def save_test(self, test: LabTest) -> None:
        self._raw[str(test.test_id)] = self._serialize(test)
        self._persist()

    def delete_test(self, test_id: int) -> bool:
        key = str(test_id)
        if key not in self._raw:
            return False
        del self._raw[key]
        self._persist()
        return True

    def get_raw(self, test_id: int) -> Optional[dict]:
        return self._raw.get(str(test_id))

    def list_raw(self) -> List[dict]:
        return list(self._raw.values())

    def backup(self, target_path: str) -> bool:
        try:
            with open(self._file_path, "r", encoding="utf-8") as src:
                data = src.read()
            with open(target_path, "w", encoding="utf-8") as dst:
                dst.write(data)
            return True
        except Exception:
            return False

    def _serialize(self, test: LabTest) -> dict:
        base = test.summary()
        base["__class__"] = type(test).__name__

        if isinstance(test.result, NumericResult):
            base["result"] = test.result.as_dict()
        else:
            base["result"] = test.result
        return base

    def _load(self) -> None:
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                self._raw = json.load(f)
        except FileNotFoundError:
            self._raw = {}
        except json.JSONDecodeError:
            self._raw = {}

    def _persist(self) -> None:
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(self._raw, f, ensure_ascii=False, indent=2)

    @classmethod
    def from_path(cls, file_path: str) -> "JsonFileLabTestRepository":
        return cls(file_path=file_path)


"""ana repo + cache"""
class CachedLabTestRepository:


    def __init__(self, main_repo: InMemoryLabTestRepository, capacity: int = 128) -> None:
        self._main = main_repo
        self._capacity = max(1, int(capacity))
        self._cache: Dict[int, LabTest] = {}
        self._hits: Dict[int, int] = {}

    def get(self, test_id: int) -> Optional[LabTest]:
        if test_id in self._cache:
            self._hits[test_id] = self._hits.get(test_id, 0) + 1
            return self._cache[test_id]

        test = self._main.get(test_id)
        if test is not None:
            self._cache_put(test_id, test)
        return test

    def add(self, test: LabTest) -> bool:
        ok = self._main.add(test)
        if ok:
            self._cache_put(test.test_id, test)
        return ok

    def delete(self, test_id: int) -> bool:
        ok = self._main.delete(test_id)
        if ok:
            self._cache.pop(test_id, None)
            self._hits.pop(test_id, None)
        return ok

    def _cache_put(self, test_id: int, test: LabTest) -> None:
        if len(self._cache) >= self._capacity:
            self._evict()
        self._cache[test_id] = test
        self._hits[test_id] = self._hits.get(test_id, 0) + 1

    def _evict(self) -> None:
        if not self._hits:
            self._cache.clear()
            return

        victim = min(self._hits.items(), key=lambda kv: kv[1])[0]
        self._cache.pop(victim, None)
        self._hits.pop(victim, None)
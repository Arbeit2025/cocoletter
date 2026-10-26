import importlib.util
import os
import tempfile
import unittest

APP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"
)


def load_app(db_path):
    os.environ["COCOLETTER_DB_PATH"] = db_path
    spec = importlib.util.spec_from_file_location("cocoletter_app", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CocoletterTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(self.db_path)
        self.mod = load_app(self.db_path)
        self.client = self.mod.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_index_ok(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Coco", res.get_data(as_text=True))

    def test_add_and_list(self):
        self.client.post("/add", data={"content": "hello memo"})
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("hello memo", body)

    def test_add_empty_is_ignored(self):
        self.client.post("/add", data={"content": "   "})
        self.assertEqual(self.mod.db_fetch(), [])

    def test_delete_via_post(self):
        self.client.post("/add", data={"content": "to delete"})
        mid = self.mod.db_fetch()[0][0]
        self.client.post(f"/delete/{mid}")
        body = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("to delete", body)

    def test_delete_get_not_allowed(self):
        res = self.client.get("/delete/1")
        self.assertEqual(res.status_code, 405)


if __name__ == "__main__":
    unittest.main()

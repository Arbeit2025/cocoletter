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

    def test_index_has_edit_link(self):
        self.client.post("/add", data={"content": "editable memo"})
        mid = self.mod.db_fetch()[0][0]
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn(f"/edit/{mid}", body)

    def test_edit_page_shows_current_content(self):
        self.client.post("/add", data={"content": "before edit"})
        mid = self.mod.db_fetch()[0][0]
        res = self.client.get(f"/edit/{mid}")
        self.assertEqual(res.status_code, 200)
        self.assertIn("before edit", res.get_data(as_text=True))

    def test_edit_via_post_updates_content(self):
        self.client.post("/add", data={"content": "before edit"})
        mid, _content, created_at = self.mod.db_fetch()[0]
        res = self.client.post(f"/edit/{mid}", data={"content": "after edit"})
        self.assertEqual(res.status_code, 302)
        row = self.mod.db_fetch_one(mid)
        self.assertEqual(row[1], "after edit")
        # created_at is preserved by an edit
        self.assertEqual(row[2], created_at)
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("after edit", body)
        self.assertNotIn("before edit", body)

    def test_edit_empty_is_ignored(self):
        self.client.post("/add", data={"content": "keep me"})
        mid = self.mod.db_fetch()[0][0]
        self.client.post(f"/edit/{mid}", data={"content": "   "})
        self.assertEqual(self.mod.db_fetch_one(mid)[1], "keep me")

    def test_edit_missing_memo_returns_404(self):
        self.assertEqual(self.client.get("/edit/9999").status_code, 404)
        res = self.client.post("/edit/9999", data={"content": "x"})
        self.assertEqual(res.status_code, 404)

    def test_cocoa_button_lines_variety(self):
        import re

        with open(APP_PATH, encoding="utf-8") as f:
            source = f.read()
        match = re.search(r"const lines=\[(.*?)\];", source, re.S)
        self.assertIsNotNone(match)
        lines = re.findall(r'"([^"]+)"', match.group(1))
        self.assertGreaterEqual(len(lines), 20)
        self.assertEqual(len(lines), len(set(lines)), "lines must be unique")
        body = self.client.get("/").get_data(as_text=True)
        for line in lines:
            self.assertIn(line, body)


if __name__ == "__main__":
    unittest.main()

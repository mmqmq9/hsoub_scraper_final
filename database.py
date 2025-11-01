import sqlite3
import pandas as pd
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = "hsoub_scraper.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                text_content TEXT,
                category TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                source_url TEXT,
                author TEXT,
                votes INTEGER DEFAULT 0,
                tags TEXT,
                full_content TEXT,
                is_enhanced INTEGER DEFAULT 0,
                data_hash TEXT UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                items_count INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                error_message TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                url TEXT NOT NULL,
                frequency TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_run DATETIME,
                next_run DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhanced_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_url TEXT NOT NULL,
                title TEXT,
                author TEXT,
                post_date TEXT,
                main_content TEXT,
                total_comments INTEGER DEFAULT 0,
                votes INTEGER DEFAULT 0,
                tags TEXT,
                question_type TEXT,
                content_quality_score REAL DEFAULT 0,
                comments_json TEXT,
                extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                training_ready INTEGER DEFAULT 0
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraped_at ON scraped_data(scraped_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON scraped_data(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_ready ON enhanced_training_data(training_ready)")

        conn.commit()
        conn.close()

    def _hash_content(self, text: str) -> str:
        return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

    def save_scraped_data(self, data: List[Dict], source_url: str = ""):
        conn = self._get_connection()
        cursor = conn.cursor()
        for item in data:
            txt = item.get("text_content") or item.get("full_content") or ""
            data_hash = self._hash_content(txt)
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO scraped_data
                    (title, link, text_content, category, source_url, scraped_at, author, votes, tags, full_content, is_enhanced, data_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("title",""),
                    item.get("link",""),
                    item.get("text_content",""),
                    item.get("category","عام"),
                    source_url,
                    item.get("scraped_at", datetime.utcnow().isoformat()),
                    item.get("author",""),
                    item.get("votes",0),
                    json.dumps(item.get("tags",[]), ensure_ascii=False),
                    item.get("full_content",""),
                    int(item.get("is_enhanced", False)),
                    data_hash
                ))
            except Exception as e:
                # skip problematic rows but keep running
                print("DB save error:", e)
        conn.commit()
        conn.close()

    def save_enhanced_training_data(self, data: Dict):
        conn = self._get_connection()
        cursor = conn.cursor()
        comments_json = json.dumps(data.get("comments", []), ensure_ascii=False)
        tags_json = json.dumps(data.get("tags", []), ensure_ascii=False)
        cursor.execute("""
            INSERT INTO enhanced_training_data
            (post_url, title, author, post_date, main_content, total_comments, votes, tags, question_type, content_quality_score, comments_json, training_ready)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("url",""),
            data.get("title",""),
            data.get("author",""),
            data.get("date",""),
            data.get("main_content",""),
            data.get("total_comments",0),
            data.get("votes",0),
            tags_json,
            data.get("question_type","عام"),
            data.get("content_quality_score",0.0),
            comments_json,
            int(bool(data.get("training_ready", False)))
        ))
        conn.commit()
        conn.close()

    def add_scrape_history(self, url: str, status: str, items_count: int = 0, duration: float = 0, error_message: Optional[str] = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scrape_history (url, status, items_count, duration_seconds, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (url, status, items_count, duration, error_message))
        conn.commit()
        conn.close()

    def get_all_scraped_data(self, limit: int = 1000) -> pd.DataFrame:
        conn = self._get_connection()
        query = "SELECT * FROM scraped_data ORDER BY scraped_at DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df

    def get_enhanced_training_data(self, limit: int = 1000) -> pd.DataFrame:
        conn = self._get_connection()
        query = "SELECT * FROM enhanced_training_data ORDER BY extracted_at DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df

    def search_scraped_data(self, search_term: str) -> pd.DataFrame:
        conn = self._get_connection()
        pattern = f"%{search_term}%"
        query = """
            SELECT * FROM scraped_data
            WHERE title LIKE ? OR text_content LIKE ? OR category LIKE ?
            ORDER BY scraped_at DESC
        """
        df = pd.read_sql_query(query, conn, params=(pattern, pattern, pattern))
        conn.close()
        return df

    def filter_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        conn = self._get_connection()
        query = """
            SELECT * FROM scraped_data
            WHERE DATE(scraped_at) BETWEEN ? AND ?
            ORDER BY scraped_at DESC
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df

    def get_scrape_history(self, limit: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        query = "SELECT * FROM scrape_history ORDER BY scraped_at DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df

    def get_statistics(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM scraped_data")
        stats['total_items'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM scrape_history")
        stats['total_scrapes'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM scrape_history WHERE status = 'success'")
        stats['successful_scrapes'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM scrape_history WHERE status = 'failed'")
        stats['failed_scrapes'] = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(items_count) FROM scrape_history WHERE status = 'success'")
        stats['avg_items_per_scrape'] = round(cursor.fetchone()[0] or 0, 2)
        cursor.execute("SELECT MAX(scraped_at) FROM scrape_history")
        stats['last_scrape'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM enhanced_training_data")
        stats['enhanced_data_count'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM enhanced_training_data WHERE training_ready = 1")
        stats['training_ready_count'] = cursor.fetchone()[0]
        conn.close()
        return stats

    def clear_all_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scraped_data")
        cursor.execute("DELETE FROM scrape_history")
        cursor.execute("DELETE FROM enhanced_training_data")
        conn.commit()
        conn.close()

    # scheduled tasks management
    def add_scheduled_task(self, task_name: str, url: str, frequency: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scheduled_tasks (task_name, url, frequency)
            VALUES (?, ?, ?)
        """, (task_name, url, frequency))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id

    def get_scheduled_tasks(self):
        conn = self._get_connection()
        df = pd.read_sql_query("SELECT * FROM scheduled_tasks ORDER BY created_at DESC", conn)
        conn.close()
        return df

    def update_task_status(self, task_id: int, is_active: bool):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE scheduled_tasks SET is_active = ? WHERE id = ?", (int(is_active), task_id))
        conn.commit()
        conn.close()

    def delete_scheduled_task(self, task_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

    def export_to_jsonl(self, filename="training_data.jsonl"):
        df = self.get_enhanced_training_data(limit=1000000)
        with open(filename, "w", encoding="utf-8") as f:
            for _, row in df.iterrows():
                comments = json.loads(row["comments_json"] or "[]")
                completion = "\\n".join([c.get("content","") for c in comments]) if comments else ""
                record = {
                    "prompt": row.get("main_content","")[:3000],
                    "completion": completion
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\\n")

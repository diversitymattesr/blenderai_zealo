import os
import sqlite3
from pydantic import BaseModel, Field
from typing import Literal, Annotated
from .utils import absolute_path, DB_DIR

class Img23DTaskIn(BaseModel):
    image_type: Literal["png", "jpeg"]
    image_token: str 
    preprocess_image: bool
    output_type: Literal["base_model", "model"]

class Img23DTask(Img23DTaskIn):

    tid: str = None
    create_status: Literal["not_yet", "creating", "creating_end", "creating_failed"] = "not_yet"
    generate_status: Literal["not_yet", "queued", "generating", "generating_end", "generating_failed"] = "not_yet"
    generate_failed_message: str | None = None
    progress: Annotated[
        int, 
        Field(ge=0, le=100)
    ] = 0
    output_url: str | None = None

class SqliteImg23dTask:

    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SqliteImg23dTask, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return 
        self.db_path = os.path.normpath(os.path.join(DB_DIR, "trellis.db"))
        self.initialized = True

    @classmethod
    def instance(cls):
        return cls()

    def create_table(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS img23d_tasks (
                tid TEXT PRIMARY KEY, 
                image_type TEXT NOT NULL CHECK(image_type IN ('png', 'jpeg')), 
                image_token TEXT NOT NULL, 
                preprocess_image INTEGER NOT NULL CHECK(preprocess_image IN (0, 1)),
                output_type TEXT NOT NULL CHECK(output_type IN ('base_model', 'model')),
                create_status TEXT NOT NULL CHECK(create_status IN ('not_yet', 'creating', 'creating_end', 'creating_failed')) DEFAULT 'not_yet',
                generate_status TEXT NOT NULL CHECK(generate_status IN ('not_yet', 'queued', 'generating', 'generating_end', 'generating_failed')) DEFAULT 'not_yet',
                generate_failed_message TEXT,
                progress INTEGER NOT NULL CHECK(progress >= 0 AND progress <= 100) DEFAULT 0,
                output_url TEXT
            ); 
        ''')
        conn.commit()
        conn.close()

    def drop_table(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            DROP TABLE IF EXISTS img23d_tasks;
        ''')
        conn.commit()
        conn.close()

    def create_item(self, task):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute('''
        INSERT INTO img23d_tasks (tid, image_type, image_token, preprocess_image, output_type)
        VALUES (?, ?, ?, ?, ?)
        ''', (task.tid, task.image_type, task.image_token, task.preprocess_image, task.output_type))
        conn.commit()
        conn.close()
    
    def update_item(self, task):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute('''
            UPDATE img23d_tasks 
            SET create_status = ?, 
                generate_status = ?,
                generate_failed_message = ?,
                progress = ?,
                output_url = ?
            WHERE tid  = ?
        ''', (task.create_status, task.generate_status, task.generate_failed_message, task.progress, task.output_url, task.tid))
        conn.commit()
        conn.close()

    def read_item(self, tid) -> Img23DTask | None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            SELECT * FROM img23d_tasks WHERE tid = ?
        ''', (tid, ))
        res = cur.fetchone()
        if res is None:
            return None
        task = Img23DTask(
            tid=res[0], 
            image_type=res[1], 
            image_token=res[2], 
            preprocess_image=res[3], 
            output_type=res[4], 
            create_status=res[5], 
            generate_status=res[6], 
            generate_failed_message=res[7], 
            progress=res[8], 
            output_url=res[9]
        )
        return task


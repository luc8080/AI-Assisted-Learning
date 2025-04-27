import sqlite3
import pandas as pd
from collections import Counter
from datetime import datetime

DB_PATH_LOG = "data_store/user_log.sqlite"
DB_PATH_QUESTIONS = "data_store/question_bank.sqlite"

# 初始化學生模型
class StudentModel:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH_LOG)
        self.df = pd.read_sql_query("SELECT * FROM answer_log ORDER BY timestamp DESC", self.conn)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df['date'] = self.df['timestamp'].dt.date

        # 額外開啟題庫連線（用於錯題主題分析）
        self.q_conn = sqlite3.connect(DB_PATH_QUESTIONS)

    def total_attempts(self):
        return len(self.df)

    def accuracy_rate(self):
        if self.df.empty:
            return 0
        return (self.df['student_answer'] == self.df['correct_answer']).mean()

    def accuracy_by_date(self):
        return self.df.groupby('date').apply(
            lambda x: (x['student_answer'] == x['correct_answer']).mean()
        ).reset_index(name='accuracy')

    def most_wrong_questions(self, topn=5):
        wrong = self.df[self.df['student_answer'] != self.df['correct_answer']]
        return wrong['question_id'].value_counts().head(topn).reset_index().rename(columns={
            'index': 'question_id',
            'question_id': 'times_wrong'
        })

    def get_wrong_topic_distribution(self):
        """統計錯題主題（需對照題庫資料）"""
        wrong_ids = self.df[self.df['student_answer'] != self.df['correct_answer']]['question_id'].tolist()
        if not wrong_ids:
            return {}

        # 把題號帶入題庫查詢主題
        q_cursor = self.q_conn.cursor()
        format_ids = ",".join([f"'{qid}'" for qid in wrong_ids])
        q_cursor.execute(f"SELECT topic FROM questions WHERE id IN ({format_ids})")
        topics = [row[0] for row in q_cursor.fetchall() if row[0]]
        return dict(Counter(topics))

    def export_summary(self):
        return {
            "答題總數": self.total_attempts(),
            "整體正確率": round(self.accuracy_rate() * 100, 1),
            "常錯題前幾名": self.most_wrong_questions().to_dict(orient="records")
        }

    def close(self):
        self.conn.close()
        self.q_conn.close()


# 範例使用
if __name__ == "__main__":
    model = StudentModel()
    print(model.export_summary())
    print(model.get_wrong_topic_distribution())
    model.close()

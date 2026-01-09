# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official


import json
import os
from logger import LOGGER

logger = LOGGER(__name__)

DB_FILE = "database.json"

class Database:
    
    def _load_db(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _save_db(self, data):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_users(self):
        return self._load_db()
    
    def new_user(self, id, name):
        return dict(
            id=id,
            name=name,
            session=None,
        )
    
    async def add_user(self, id, name):
        db = self._load_db()
        if str(id) not in db:
            user = self.new_user(id, name)
            db[str(id)] = user
            self._save_db(db)
            logger.info(f"New user added to DB: {id} - {name}")
    
    async def is_user_exist(self, id):
        db = self._load_db()
        return str(id) in db
    
    def total_users_count(self):
        db = self._load_db()
        return len(db)
    
    def get_all_users(self):
        db = self._load_db()
        for user in db.values():
            yield user
    
    def delete_user(self, user_id):
        db = self._load_db()
        if str(user_id) in db:
            del db[str(user_id)]
            self._save_db(db)
            logger.info(f"User deleted from DB: {user_id}")
    
    async def set_session(self, id, session):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["session"] = session
            self._save_db(db)
    
    async def get_session(self, id):
        db = self._load_db()
        user = db.get(str(id))
        return user.get("session") if user else None
    
    # Caption Support
    def set_caption(self, id, caption):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["caption"] = caption
            self._save_db(db)
    
    def get_caption(self, id):
        db = self._load_db()
        user = db.get(str(id))
        return user.get("caption", None) if user else None
    
    def del_caption(self, id):
        db = self._load_db()
        if str(id) in db:
            db[str(id)].pop("caption", None)
            self._save_db(db)
    
    # Thumbnail Support
    def set_thumbnail(self, id, thumbnail):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["thumbnail"] = thumbnail
            self._save_db(db)
    
    def get_thumbnail(self, id):
        db = self._load_db()
        user = db.get(str(id))
        return user.get("thumbnail", None) if user else None
    
    def del_thumbnail(self, id):
        db = self._load_db()
        if str(id) in db:
            db[str(id)].pop("thumbnail", None)
            self._save_db(db)
    
    # Premium Support
    async def add_premium(self, id, expiry_date):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["is_premium"] = True
            db[str(id)]["premium_expiry"] = expiry_date
            self._save_db(db)
            logger.info(f"User {id} granted premium until {expiry_date}")
    
    async def remove_premium(self, id):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["is_premium"] = False
            db[str(id)]["premium_expiry"] = None
            self._save_db(db)
            logger.info(f"User {id} removed from premium")
    
    async def check_premium(self, id):
        db = self._load_db()
        user = db.get(str(id))
        if user and user.get("is_premium"):
            return user.get("premium_expiry")
        return None
    
    async def get_premium_users(self):
        db = self._load_db()
        for user in db.values():
            if user.get("is_premium"):
                yield user
    
    # Ban Support
    def ban_user(self, id):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["is_banned"] = True
            self._save_db(db)
            logger.warning(f"User banned: {id}")
    
    def unban_user(self, id):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["is_banned"] = False
            self._save_db(db)
            logger.info(f"User unbanned: {id}")
    
    def is_banned(self, id):
        db = self._load_db()
        user = db.get(str(id))
        return user.get("is_banned", False) if user else False
    
    # Dump Chat Support
    def set_dump_chat(self, id, chat_id):
        db = self._load_db()
        if str(id) in db:
            db[str(id)]["dump_chat"] = int(chat_id)
            self._save_db(db)
    
    def get_dump_chat(self, id):
        db = self._load_db()
        user = db.get(str(id))
        return user.get("dump_chat", None) if user else None
    
    # Delete/Replace Words Support
    def set_delete_words(self, id, words):
        db = self._load_db()
        if str(id) in db:
            if "delete_words" not in db[str(id)]:
                db[str(id)]["delete_words"] = []
            db[str(id)]["delete_words"].extend(words)
            self._save_db(db)
    
    def get_delete_words(self, id):
        db = self._load_db()
        user = db.get(str(id))
        return user.get("delete_words", []) if user else []
    
    def remove_delete_words(self, id, words):
        db = self._load_db()
        if str(id) in db:
            if "delete_words" in db[str(id)]:
                db[str(id)]["delete_words"] = [w for w in db[str(id)]["delete_words"] if w not in words]
                self._save_db(db)
    
    def set_replace_words(self, id, repl_dict):
        db = self._load_db()
        if str(id) in db:
            if "replace_words" not in db[str(id)]:
                db[str(id)]["replace_words"] = {}
            db[str(id)]["replace_words"].update(repl_dict)
            self._save_db(db)
    
    def get_replace_words(self, id):
        db = self._load_db()
        user = db.get(str(id))
        return user.get("replace_words", {}) if user else {}
    
    def remove_replace_words(self, id, words):
        db = self._load_db()
        if str(id) in db:
            if "replace_words" in db[str(id)]:
                for w in words:
                    db[str(id)]["replace_words"].pop(w, None)
                self._save_db(db)


db = Database()


# Rexbots
# Don't Remove Credit 🥺
# Telegram Channel @RexBots_Official

# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

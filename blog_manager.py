import mysql.connector
from mysql.connector import Error

class BlogManager:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root',
                database='blog_db'
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                self.create_tables()
                
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            exit(1)
    
    def create_tables(self):
        # Create posts table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create tags table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE
        )
        """)
        
        # Create post_tags linking table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id INT NOT NULL,
            tag_id INT NOT NULL,
            PRIMARY KEY (post_id, tag_id),
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
        """)
        
        self.connection.commit()
    
    def create_post(self, title, content, tags_str):
        try:
            # Insert post
            self.cursor.execute("INSERT INTO posts (title, content) VALUES (%s, %s)", (title, content))
            post_id = self.cursor.lastrowid
            
            # Process tags
            tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
            
            for tag_name in tags:
                # Insert tag if not exists
                self.cursor.execute("INSERT IGNORE INTO tags (name) VALUES (%s)", (tag_name,))
                
                # Get tag id
                self.cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
                tag_id = self.cursor.fetchone()[0]
                
                # Link post and tag
                self.cursor.execute("INSERT INTO post_tags (post_id, tag_id) VALUES (%s, %s)", (post_id, tag_id))
            
            self.connection.commit()
            print(f"Post '{title}' created successfully with tags: {', '.join(tags)}")
            
        except Error as e:
            self.connection.rollback()
            print(f"Error creating post: {e}")
    
    def list_posts(self):
        try:
            self.cursor.execute("SELECT id, title FROM posts ORDER BY created_at DESC")
            posts = self.cursor.fetchall()
            
            if not posts:
                print("No posts found.")
                return
            
            print("\nAll Posts:")
            for post_id, title in posts:
                print(f"{post_id}. {title}")
            print()
            
        except Error as e:
            print(f"Error listing posts: {e}")
    
    def view_post(self, title):
        try:
            # Get post content
            self.cursor.execute("SELECT content FROM posts WHERE title = %s", (title,))
            post = self.cursor.fetchone()
            
            if not post:
                print(f"Post '{title}' not found.")
                return
            
            print(f"\n{title}\n{'='*len(title)}")
            print(post[0])
            
            # Get tags for the post
            self.cursor.execute("""
            SELECT t.name FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            JOIN posts p ON pt.post_id = p.id
            WHERE p.title = %s
            """, (title,))
            
            tags = [tag[0] for tag in self.cursor.fetchall()]
            print(f"\nTags: {', '.join(tags) if tags else 'No tags'}\n")
            
        except Error as e:
            print(f"Error viewing post: {e}")
    
    def search_by_tag(self, tag_name):
        try:
            self.cursor.execute("""
            SELECT p.title FROM posts p
            JOIN post_tags pt ON p.id = pt.post_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE t.name = %s
            ORDER BY p.created_at DESC
            """, (tag_name.lower(),))
            
            posts = self.cursor.fetchall()
            
            if not posts:
                print(f"No posts found with tag '{tag_name}'.")
                return
            
            print(f"\nPosts tagged with '{tag_name}':")
            for title in posts:
                print(f"- {title[0]}")
            print()
            
        except Error as e:
            print(f"Error searching by tag: {e}")
    
    def close(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

def main():
    manager = BlogManager()
    
    print("Blog Post Management System")
    print("Commands: create, list, view, search, exit")
    
    while True:
        command = input("\nEnter command: ").strip().lower()
        
        if command == 'exit':
            manager.close()
            print("Goodbye!")
            break
            
        elif command == 'create':
            title = input("Enter post title: ").strip()
            content = input("Enter post content: ").strip()
            tags = input("Enter comma-separated tags: ").strip()
            manager.create_post(title, content, tags)
            
        elif command == 'list':
            manager.list_posts()
            
        elif command == 'view':
            title = input("Enter post title to view: ").strip()
            manager.view_post(title)
            
        elif command == 'search':
            tag = input("Enter tag to search: ").strip().lower()
            manager.search_by_tag(tag)
            
        else:
            print("Invalid command. Please try again.")

if __name__ == "__main__":
    main()
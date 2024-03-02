#!/usr/bin/env python3

import argparse
import sqlite3
import os
import hashlib
from collections import defaultdict
import time
from datetime import datetime

DEFAULT_DB_FILE = "myfile.db"

def show_help(parser):
    parser.print_help()

# Function to create a connection to SQLite database
def create_connection(db_file=DEFAULT_DB_FILE):
    try:
        conn = sqlite3.connect(db_file)
        ensure_database_exists(conn)
        return conn
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

# Function to create an enhanced table in the SQLite database
def ensure_database_exists(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_info (
                path TEXT PRIMARY KEY,
                hash TEXT,
                file_type TEXT,
                size INTEGER,
                last_modified INTEGER
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error ensuring database exists: {e}")

# Function to get the hash of a file
def get_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# Function to insert or update file information in the SQLite database
def insert_or_update_file_info(conn, file_path, file_hash, file_type, file_size, last_modified):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO file_info (path, hash, file_type, size, last_modified) 
            VALUES (?, ?, ?, ?, ?)
        """, (file_path, file_hash, file_type, file_size, last_modified))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting/updating file info: {e}")

# Function to collect file information
def collect_file_info(file_path):
    file_hash = get_file_hash(file_path)
    file_type = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
    file_size = os.path.getsize(file_path)
    last_modified = int(os.path.getmtime(file_path))
    return file_hash, file_type, file_size, last_modified

# Function to find duplicate files with enhanced information
def find_duplicates_with_enhanced_info(conn, root_directory, file_types):
    duplicates = defaultdict(list)
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in file_types):
                file_path = os.path.join(dirpath, filename)
                file_hash, file_type, file_size, last_modified = collect_file_info(file_path)
                insert_or_update_file_info(conn, file_path, file_hash, file_type, file_size, last_modified)
                duplicates[file_hash].append(file_path)

    return {hash: paths for hash, paths in duplicates.items() if len(paths) > 1}

# Function to find files by date range
def find_files_by_date(conn, start_date, end_date=None):
    files = []
    try:
        cursor = conn.cursor()
        query = "SELECT path FROM file_info WHERE last_modified >= ?"
        params = [start_date]

        if end_date:
            query += " AND last_modified <= ?"
            params.append(end_date)

        cursor.execute(query, params)
        files = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Error finding files by date: {e}")

    return files

# Function to find large files
def find_large_files(conn, size_threshold):
    large_files = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM file_info WHERE size > ?", (size_threshold,))
        large_files = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Error finding large files: {e}")

    return large_files

# Function to find large files with details 
def find_large_files_with_details(conn, size_threshold):
    """
    Find large files and provide details including file size and last modified date in human-readable format.
    :param conn: Connection to the SQLite database
    :param size_threshold: Size threshold in bytes
    :return: List of tuples containing file details
    """
    large_files_details = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT path, size, last_modified 
            FROM file_info 
            WHERE size > ?
        """, (size_threshold,))
        
        for row in cursor.fetchall():
            path, size, last_modified = row
            last_modified_date = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')
            large_files_details.append((path, size, last_modified_date))

    except sqlite3.Error as e:
        print(f"Error finding large files: {e}")

    return large_files_details

# Function to clean old files
def clean_old_files(conn, last_accessed_threshold):
    cleaned_files = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM file_info WHERE last_modified < ?", (last_accessed_threshold,))
        old_files = [row[0] for row in cursor.fetchall()]

        for file in old_files:
            if os.path.exists(file):
                os.remove(file)
                cleaned_files.append(file)

        # Removing deleted files from database
        cursor.executemany("DELETE FROM file_info WHERE path = ?", [(file,) for file in cleaned_files])
        conn.commit()

    except sqlite3.Error as e:
        print(f"Error cleaning old files: {e}")

    return cleaned_files

# Function to delete duplicates and update database
def delete_duplicates_and_update_db_interactive(conn, file_list):
    """
    Interactively delete specified duplicate files and update the database accordingly.
    :param conn: Connection to the SQLite database
    :param file_list: List of file paths to potentially delete
    :return: List of deleted file paths
    """
    deleted_files = []
    try:
        for file_hash, paths in file_list.items():
            print(f"\nDuplicate files for hash {file_hash}:")
            for i, path in enumerate(paths, 1):
                print(f"{i}. {path}")

            choice = input("Enter the number of the file you want to KEEP (others will be deleted) press [ENTER] to skip: ")
            try:
                choice = int(choice)
                if 1 <= choice <= len(paths):
                    for i, path in enumerate(paths, 1):
                        if i != choice and os.path.exists(path):
                            os.remove(path)
                            deleted_files.append(path)
                            print(f"Deleted file: {path}")
                    # Updating the database
                    keep_path = paths[choice - 1]
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM file_info WHERE path != ? AND hash = ?", (keep_path, file_hash))
                    conn.commit()
                else:
                    print("Invalid choice. Skipping these files.")
            except ValueError:
                print("Invalid input. Skipping these files.")

    except sqlite3.Error as e:
        print(f"Error deleting files and updating database: {e}")
    return deleted_files

# Get statistics from the SQLite database.
def get_statistics(conn):
    """
    Get statistics from the SQLite database.
    :param conn: Connection object to the SQLite database
    :return: Statistics as a dictionary
    """
    stats = {}
    try:
        cursor = conn.cursor()
        
        # Total number of files
        cursor.execute("SELECT COUNT(*) FROM file_info")
        stats['total_files'] = cursor.fetchone()[0]

        # Total number of unique file types
        cursor.execute("SELECT COUNT(DISTINCT file_type) FROM file_info")
        stats['unique_file_types'] = cursor.fetchone()[0]

        # File type distribution
        cursor.execute("SELECT file_type, COUNT(*) FROM file_info GROUP BY file_type")
        stats['file_type_distribution'] = dict(cursor.fetchall())

        # Total size of all files
        cursor.execute("SELECT SUM(size) FROM file_info")
        stats['total_size'] = cursor.fetchone()[0]

    except sqlite3.Error as e:
        print(f"Error retrieving statistics: {e}")

    return stats
#Function Show duplicate files
def show_duplicate_files(conn):
    """
    Show duplicate files stored in the database.
    :param conn: Connection to the SQLite database
    :return: Dictionary of duplicates where key is the hash and value is a list of file paths
    """
    duplicates = defaultdict(list)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, GROUP_CONCAT(path, ', ') 
            FROM file_info 
            GROUP BY hash 
            HAVING COUNT(*) > 1
        """)
        
        for row in cursor.fetchall():
            file_hash, paths = row
            duplicates[file_hash] = paths.split(', ')

    except sqlite3.Error as e:
        print(f"Error retrieving duplicate files: {e}")

    return duplicates

#Function GodFather :) 
def execute_command(args, conn):
    if args.command == 'create-db':
        create_enhanced_table(conn)
    elif args.command == 'find-duplicates':
        duplicates = find_duplicates_with_enhanced_info(conn, args.directory, args.file_types)
        for hash, paths in duplicates.items():
            print(f"Duplicate files for hash {hash}:")
            for path in paths:
                print(f" - {path}")
    elif args.command == 'find-by-date':
        files = find_files_by_date(conn, args.start_date, args.end_date)
        for file in files:
            print(file)
    elif args.command == 'find-large-files':
            large_files_details = find_large_files_with_details(conn, args.size_threshold)
            for file_detail in large_files_details:
                print(f"File: {file_detail[0]}, Size: {file_detail[1]} bytes, Last Modified: {file_detail[2]}")
    elif args.command == 'clean-old-files':
        cleaned_files = clean_old_files(conn, args.last_accessed_threshold)
        for file in cleaned_files:
            print(f"Cleaned (deleted) file: {file}")
    elif args.command == 'delete-duplicates':
        deleted_files = delete_duplicates_and_update_db(conn, args.file_list)
        for file in deleted_files:
            print(f"Deleted file: {file}")
    elif args.command == 'stats':
            statistics = get_statistics(conn)
            for key, value in statistics.items():
                print(f"{key}: {value}")
    elif args.command == 'show-duplicates':
            duplicates = show_duplicate_files(conn)
            for hash, paths in duplicates.items():
                print(f"Duplicate files for hash {hash}:")
                for path in paths:
                    print(f" - {path}")
    elif args.command == 'delete-duplicates-interactive':
            duplicates = show_duplicate_files(conn)
            if duplicates:
                delete_duplicates_and_update_db_interactive(conn, duplicates)
            else:
                print("No duplicates found.")
    elif not args.command:
        parser.print_help()
    

# Main function to handle command line arguments
def main():
    parser = argparse.ArgumentParser(description="File Duplicate Finder and Manager by _MYFOX_ - Licensed under GNU",
                                     usage="%(prog)s [command] [<args>]",
                                     formatter_class=argparse.RawTextHelpFormatter)
    subparsers = parser.add_subparsers(dest="command")


    # Create DB command
    create_db_parser = subparsers.add_parser('create-db', help='Create or initialize the database')
    create_db_parser.add_argument('db_file', type=str, nargs='?', default=DEFAULT_DB_FILE, help='Path to the SQLite database file')
    create_db_parser.description = "Create or initialize the SQLite database."

    # Find duplicates command
    find_dup_parser = subparsers.add_parser('find-duplicates', help='Find duplicate files')
    find_dup_parser.add_argument('db_file', type=str, nargs='?', default=DEFAULT_DB_FILE, help='Path to the SQLite database file')
    find_dup_parser.add_argument('directory', type=str, help='Directory to search for duplicate files')
    find_dup_parser.add_argument('file_types', nargs='+', help='File types to search for')
    find_dup_parser.description = "Find duplicate files"

    # Find files by date command
    find_date_parser = subparsers.add_parser('find-by-date', help='Find files by date range')
    find_date_parser.add_argument('db_file', type=str, nargs='?', default=DEFAULT_DB_FILE, help='Path to the SQLite database file')
    find_date_parser.add_argument('start_date', type=int, help='Start date timestamp')
    find_date_parser.add_argument('--end_date', type=int, help='End date timestamp', default=None)
    find_date_parser.description = "Find files by date range using timestamp'"

    # Find large files command
    find_large_parser = subparsers.add_parser('find-large-files', help='Find large files with details')
    find_large_parser.add_argument('db_file', type=str, nargs='?', default=DEFAULT_DB_FILE, help='Path to the SQLite database file')
    find_large_parser.add_argument('size_threshold', type=int, help='Size threshold in bytes')
    find_large_parser.description = "Find large files with details in bytes"

    # Clean old files command
    clean_old_parser = subparsers.add_parser('clean-old-files', help='Clean old or unused files')
    clean_old_parser.add_argument('db_file', type=str,  nargs='?', default=DEFAULT_DB_FILE, help='Path to the SQLite database file')
    clean_old_parser.add_argument('last_accessed_threshold', type=int, help='Last accessed time threshold (timestamp)')
    clean_old_parser.description = "Clean old or unused files"

    # Delete duplicates command (interactive)
    delete_dup_parser = subparsers.add_parser('delete-duplicates-interactive', help='Interactively delete duplicate files')
    delete_dup_parser.add_argument('db_file', type=str, nargs='?', default=DEFAULT_DB_FILE, help='Path to the SQLite database file')
    delete_dup_parser.description = "Interactively delete duplicate files"

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics about files')
    stats_parser.add_argument('db_file', type=str, nargs='?', default=DEFAULT_DB_FILE, help='Path to the SQLite database file')
    stats_parser.description = "Show statistics about files on DB"

    # Show duplicates command
    show_dup_parser = subparsers.add_parser('show-duplicates', help='Show duplicate files stored in the database')
    show_dup_parser.add_argument('db_file', type=str,  nargs='?', default=DEFAULT_DB_FILE,help='Path to the SQLite database file')
    show_dup_parser.description = "Show duplicate files stored in the database"

    # Help command
#    help_parser = subparsers.add_parser('help', help='Show help for commands')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
    else:
        conn = create_connection(args.db_file if 'db_file' in args else DEFAULT_DB_FILE)
        if conn:
            execute_command(args, conn)
        pass

# Uncomment the following line to enable command line functionality
if __name__ == "__main__":
    main()

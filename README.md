# File Duplicate Finder and Manager
## deduplica

This tool is designed to help manage and organize files by finding and handling duplicate files on your system. It’s a beta version so don’t use it in production environments, or first try it on a test folder
I am not responsible for your damages :)

## Prerequisites

- Python 3.x
- SQLite3

## Installation

Clone the repository or download the files directly to your local machine.

## Usage

Run the script from the command line. The [db_file] parameter is optional. If it is not specified at the first run of the script, the DB "myfile.db" is created and used by default. It is possible to create more DB depending on the case and the needs, giving the possibility to have different DB depending on the use cases.
Here are the available commands:

1. **Create Database (`create-db`)**
   - `python deduplica.py create-db [db_file]`
   - Creates or initializes the database. If no database file is specified, `myfile.db` is used as default.

2. **Find Duplicates (`find-duplicates`)**
   - `python deduplica.py find-duplicates [db_file] <directory> <file_types>`
   - Find duplicate files. Search the specified file type in the folder and insert them into the DB

3. **Find Files by Date (`find-by-date`)**
   - `python deduplica.py find-by-date [db_file] <start_date> [--end_date <end_date>]`
   - Finds files modified within the given date range. Dates should be in Unix timestamp format.

4. **Find Large Files (`find-large-files`)**
   - `python deduplica.py find-large-files [db_file] <size_threshold>`
   - Finds files larger than the specified size threshold.

5. **Clean Old Files (`clean-old-files`)**
   - `python deduplica.py clean-old-files [db_file] <last_accessed_threshold>`
   - Cleans files that haven't been accessed since the specified threshold.

6. **Delete Duplicates Interactively (`delete-duplicates-interactive`)**
   - `python deduplica.py delete-duplicates-interactive [db_file] [<file_types>]`
   - Interactively handles the deletion of duplicate files.

7. **Show Duplicate Files (`show-duplicates`)**
   - `python deduplica.py show-duplicates [db_file]`
   - Displays duplicate files stored in the database.
  

## How Can This Tool Be Useful?

- Organize large collections of files such as photos, videos, or documents.
- Reclaim disk space by removing unnecessary duplicate files.
- Simplify file management tasks.


## Credits

This tool was developed by _MYFOX_. For any queries or suggestions, please feel free to contact.

## Contributing

Contributions to the codebase are welcome! Feel free to fork the repository and submit pull requests.

## Donations

If you find this tool helpful and would like to support its development, donations are appreciated. 
DOGE DN4MEB5L41u98EP99cpTgZXt1QbEfQUVJx

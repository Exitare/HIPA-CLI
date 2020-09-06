from Shared.Database import Database_Loader
import os
from Shared.Database.PreparedStatement import PreparedStatement
from Shared.Database import Database
from Shared.Database.Implementation import Queries
import datetime
import logging
import sys
from pathlib import Path


def create_db():
    """
    Creates all schemas and tables required to operate the server
    Returns
    -------

    """

    try:
        base_path: Path = Path("./SQL/Base")
        logging.info("Creating database schema if necessary")
        for filename in os.listdir(base_path):
            if filename.endswith(".sql"):
                __execute_file(Path(base_path, filename))

    except BaseException as ex:
        logging.exception(ex)
        sys.exit()


def update_db():
    """
    Updates the database
    :return:
    """
    logging.info("Updating database....")
    update_path: Path = Path("./SQL/Updates")
    for filename in os.listdir(update_path):
        if filename.endswith(".sql") and not __update_already_applied(filename):
            __execute_file(Path(update_path, filename))
        else:
            continue
    logging.info("Database up to date!")


def __execute_file(file_path: Path):
    """
    Reads the file and execute its queries
    :param file_path:
    :return:
    """
    # Open and read the file as a single buffer
    fd = open(file_path, 'r')
    sql_content = fd.read()
    fd.close()

    # all SQL commands (split on ';')
    sql_commands = sql_content.split(';')

    # create db cursor
    connection = Database_Loader.databasePool.get_connection()
    cursor = connection.cursor(prepared=False)
    error_count: int = 0
    # Execute every command from the input file
    for command in sql_commands:
        # This will skip and report errors
        # For example, if the tables do not yet exist, this will skip over
        # the DROP TABLE commands
        try:
            cursor.execute(command)
        except BaseException as msg:
            print(f"Command skipped: {msg}")
            error_count += 1

    connection.commit()
    if error_count == 0:
        __update_successful_applied(file_path)


def __update_already_applied(filename):
    statement = PreparedStatement(Queries.DB_SEL_UPDATE)
    statement.add_param(0, filename)
    data = Database.select(statement)
    if data[0][0] == 1:
        return True
    else:
        return False


def __update_successful_applied(filename: str):
    """
    Adds an successful update file to the updates table
    :param filename:
    :return:
    """
    statement = PreparedStatement(Queries.DB_INS_UPDATE)
    statement.add_param(0, filename)
    statement.add_param(1, 0)
    statement.add_param(2, "RELEASED")
    statement.add_param(3, datetime.datetime.utcnow())
    statement.add_param(4, 0)
    Database.insert(statement)
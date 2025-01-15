import snowflake.connector
import os
from typing import Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Snowflake connection parameters
SNOWFLAKE_CONFIG = {
    "account": "Add_your_account",
    "user": "Add_your_user",
    "password": "Add_your_password",
    "database": "Add_your_database",
    "schema": "Add_your_schema",
    "warehouse": "Add_your_warehouse"
}

def upload_to_stage(local_folder: str, file_extensions: Tuple[str, ...] = (".pdf",)) -> List[str]:
    """
    Uploads files from a local folder to a Snowflake stage.

    Args:
        local_folder (str): Path to the local folder containing files to upload
        file_extensions (tuple): Tuple of file extensions to filter files (default: (".pdf",))

    Returns:
        List[str]: List of successfully uploaded files
    """
    if not os.path.exists(local_folder):
        raise FileNotFoundError(f"Folder not found: {local_folder}")

    uploaded_files = []

    try:
        # Connect to Snowflake
        ctx = snowflake.connector.connect(
            account=SNOWFLAKE_CONFIG["account"],
            user=SNOWFLAKE_CONFIG["user"],
            password=SNOWFLAKE_CONFIG["password"],
            database=SNOWFLAKE_CONFIG["database"],
            schema=SNOWFLAKE_CONFIG["schema"],
            warehouse=SNOWFLAKE_CONFIG["warehouse"]
        )
        cursor = ctx.cursor()

        # Set context
        cursor.execute(f"USE DATABASE {SNOWFLAKE_CONFIG['database']}")
        cursor.execute(f"USE SCHEMA {SNOWFLAKE_CONFIG['schema']}")
        cursor.execute(f"USE WAREHOUSE {SNOWFLAKE_CONFIG['warehouse']}")

        # Verify the stage exists
        cursor.execute("SHOW STAGES")
        stages = cursor.fetchall()
        stage_names = [stage[1] for stage in stages]  # Stage names are in the second column
        if "DOCS" not in stage_names:
            logger.error("Stage 'DOCS' does not exist. Please create it first.")
            raise ValueError("Stage 'DOCS' does not exist.")

        # Get the list of files to upload
        files_to_upload = [
            os.path.join(local_folder, f)
            for f in os.listdir(local_folder)
            if f.lower().endswith(tuple(ext.lower() for ext in file_extensions))
        ]

        if not files_to_upload:
            logger.warning(f"No files found with extensions {file_extensions} in {local_folder}")
            return uploaded_files

        # Upload each file to the stage
        for file_path in files_to_upload:
            try:
                logger.info(f"Uploading {file_path}...")
                # Using the stage name 'DOCS' that we confirmed exists
                put_command = f"PUT 'file://{file_path}' @DOCS AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
                logger.info(f"Executing command: {put_command}")
                cursor.execute(put_command)
                uploaded_files.append(file_path)
                logger.info(f"Successfully uploaded {file_path}")
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {str(e)}")

        return uploaded_files

    except snowflake.connector.errors.ProgrammingError as e:
        logger.error(f"Snowflake connection error: {str(e)}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'ctx' in locals():
            ctx.close()

if __name__ == "__main__":
    try:
        folder_path = "your_folder_path"
        uploaded_files = upload_to_stage(folder_path)
        if uploaded_files:
            logger.info(f"Successfully uploaded {len(uploaded_files)} files")
            logger.info("Uploaded files:")
            for file in uploaded_files:
                logger.info(f"- {file}")
        else:
            logger.warning("No files were uploaded")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
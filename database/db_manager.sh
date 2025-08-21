#!/bin/bash
# ============================================
# EcoBot Database Management Script
# Desa Cukangkawung Waste Management System
# ============================================

DB_PATH="/home/azureuser/ecobot/database/ecobot.db"
SCHEMA_FILE="/home/azureuser/ecobot/database/schema.sql"
DUMMY_DATA_FILE="/home/azureuser/ecobot/database/dummy_data.sql"
BACKUP_DIR="/home/azureuser/ecobot/database/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

show_help() {
    echo -e "${BLUE}EcoBot Database Management Script${NC}"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  init       Initialize new database with schema"
    echo "  reset      Reset database (backup current, create new)"
    echo "  seed       Load dummy data into existing database"
    echo "  backup     Create backup of current database"
    echo "  restore    Restore from latest backup"
    echo "  status     Show database status and table counts"
    echo "  test       Test database connection and structure"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 init     # Create new database"
    echo "  $0 reset    # Reset and reload everything"
    echo "  $0 seed     # Load dummy data only"
    echo "  $0 status   # Check current database status"
}

backup_database() {
    if [ -f "$DB_PATH" ]; then
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        BACKUP_FILE="$BACKUP_DIR/ecobot_backup_$TIMESTAMP.db"
        cp "$DB_PATH" "$BACKUP_FILE"
        echo -e "${GREEN}Database backed up to: $BACKUP_FILE${NC}"
        return 0
    else
        echo -e "${YELLOW}No database file found to backup${NC}"
        return 1
    fi
}

init_database() {
    echo -e "${BLUE}Initializing new database...${NC}"
    
    if [ -f "$DB_PATH" ]; then
        echo -e "${YELLOW}Database already exists. Use 'reset' to recreate.${NC}"
        return 1
    fi
    
    if [ ! -f "$SCHEMA_FILE" ]; then
        echo -e "${RED}Schema file not found: $SCHEMA_FILE${NC}"
        return 1
    fi
    
    sqlite3 "$DB_PATH" < "$SCHEMA_FILE"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database initialized successfully!${NC}"
        return 0
    else
        echo -e "${RED}Failed to initialize database${NC}"
        return 1
    fi
}

reset_database() {
    echo -e "${BLUE}Resetting database...${NC}"
    
    # Backup existing database
    backup_database
    
    # Remove existing database
    if [ -f "$DB_PATH" ]; then
        rm "$DB_PATH"
        echo -e "${YELLOW}Existing database removed${NC}"
    fi
    
    # Initialize new database
    init_database
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database reset completed!${NC}"
        return 0
    else
        return 1
    fi
}

seed_database() {
    echo -e "${BLUE}Loading dummy data...${NC}"
    
    if [ ! -f "$DB_PATH" ]; then
        echo -e "${RED}Database not found. Run 'init' first.${NC}"
        return 1
    fi
    
    if [ ! -f "$DUMMY_DATA_FILE" ]; then
        echo -e "${RED}Dummy data file not found: $DUMMY_DATA_FILE${NC}"
        return 1
    fi
    
    sqlite3 "$DB_PATH" < "$DUMMY_DATA_FILE"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Dummy data loaded successfully!${NC}"
        return 0
    else
        echo -e "${RED}Failed to load dummy data${NC}"
        return 1
    fi
}

restore_database() {
    echo -e "${BLUE}Restoring from backup...${NC}"
    
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/ecobot_backup_*.db 2>/dev/null | head -n1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        echo -e "${RED}No backup files found in $BACKUP_DIR${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Restoring from: $LATEST_BACKUP${NC}"
    
    # Backup current database before restore
    if [ -f "$DB_PATH" ]; then
        backup_database
    fi
    
    cp "$LATEST_BACKUP" "$DB_PATH"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database restored successfully!${NC}"
        return 0
    else
        echo -e "${RED}Failed to restore database${NC}"
        return 1
    fi
}

show_status() {
    echo -e "${BLUE}Database Status${NC}"
    echo "============================================"
    
    if [ ! -f "$DB_PATH" ]; then
        echo -e "${RED}Database file not found: $DB_PATH${NC}"
        return 1
    fi
    
    echo -e "Database file: ${GREEN}$DB_PATH${NC}"
    echo -e "File size: $(du -h "$DB_PATH" | cut -f1)"
    echo -e "Last modified: $(stat -c %y "$DB_PATH" | cut -d. -f1)"
    echo ""
    
    echo -e "${BLUE}Table Counts:${NC}"
    echo "----------------------------------------"
    
    sqlite3 "$DB_PATH" "
    SELECT 
        'Users: ' || COUNT(*) || ' total, ' || 
        SUM(CASE WHEN role='admin' THEN 1 ELSE 0 END) || ' admin, ' ||
        SUM(CASE WHEN role='koordinator' THEN 1 ELSE 0 END) || ' koordinator, ' ||
        SUM(CASE WHEN role='warga' THEN 1 ELSE 0 END) || ' warga'
    FROM users;
    
    SELECT 'Collection Points: ' || COUNT(*) || ' total, ' || 
           SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) || ' active'
    FROM collection_points;
    
    SELECT 'Collection Schedules: ' || COUNT(*) FROM collection_schedules;
    
    SELECT 'Waste Classifications: ' || COUNT(*) || ' total, ' ||
           SUM(CASE WHEN DATE(created_at) = DATE('now') THEN 1 ELSE 0 END) || ' today'
    FROM waste_classifications;
    
    SELECT 'User Interactions: ' || COUNT(*) || ' total, ' ||
           SUM(CASE WHEN DATE(created_at) = DATE('now') THEN 1 ELSE 0 END) || ' today'
    FROM user_interactions;
    
    SELECT 'System Logs: ' || COUNT(*) || ' total, ' ||
           SUM(CASE WHEN level='ERROR' THEN 1 ELSE 0 END) || ' errors'
    FROM system_logs;
    "
    
    echo ""
    echo -e "${BLUE}Recent Activity (Last 24 hours):${NC}"
    echo "----------------------------------------"
    sqlite3 "$DB_PATH" "
    SELECT 
        'New users: ' || COUNT(*) 
    FROM users 
    WHERE DATE(first_seen) >= DATE('now', '-1 day');
    
    SELECT 
        'Classifications: ' || COUNT(*) 
    FROM waste_classifications 
    WHERE DATE(created_at) >= DATE('now', '-1 day');
    
    SELECT 
        'Interactions: ' || COUNT(*) 
    FROM user_interactions 
    WHERE DATE(created_at) >= DATE('now', '-1 day');
    "
}

test_database() {
    echo -e "${BLUE}Testing database connection and structure...${NC}"
    echo "============================================"
    
    if [ ! -f "$DB_PATH" ]; then
        echo -e "${RED}Database file not found: $DB_PATH${NC}"
        return 1
    fi
    
    # Test basic connection
    if sqlite3 "$DB_PATH" "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
    else
        echo -e "${RED}✗ Database connection failed${NC}"
        return 1
    fi
    
    # Test table existence
    EXPECTED_TABLES=("users" "collection_points" "collection_schedules" "waste_classifications" "user_interactions" "system_logs")
    
    echo ""
    echo -e "${BLUE}Table Structure Test:${NC}"
    for table in "${EXPECTED_TABLES[@]}"; do
        if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table';" | grep -q "$table"; then
            echo -e "${GREEN}✓ Table '$table' exists${NC}"
        else
            echo -e "${RED}✗ Table '$table' missing${NC}"
        fi
    done
    
    # Test indexes
    echo ""
    echo -e "${BLUE}Index Test:${NC}"
    INDEX_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';")
    echo -e "Found $INDEX_COUNT custom indexes"
    
    # Test triggers
    echo ""
    echo -e "${BLUE}Trigger Test:${NC}"
    TRIGGER_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger';")
    echo -e "Found $TRIGGER_COUNT triggers"
    
    # Test data integrity
    echo ""
    echo -e "${BLUE}Data Integrity Test:${NC}"
    
    # Check for orphaned records
    ORPHANED_CLASSIFICATIONS=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM waste_classifications w 
    LEFT JOIN users u ON w.user_phone = u.phone_number 
    WHERE u.phone_number IS NULL;")
    
    ORPHANED_INTERACTIONS=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM user_interactions i 
    LEFT JOIN users u ON i.user_phone = u.phone_number 
    WHERE u.phone_number IS NULL;")
    
    if [ "$ORPHANED_CLASSIFICATIONS" -eq 0 ] && [ "$ORPHANED_INTERACTIONS" -eq 0 ]; then
        echo -e "${GREEN}✓ No orphaned records found${NC}"
    else
        echo -e "${YELLOW}⚠ Found $ORPHANED_CLASSIFICATIONS orphaned classifications and $ORPHANED_INTERACTIONS orphaned interactions${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Database test completed!${NC}"
}

# Main script logic
case "${1:-help}" in
    "init")
        init_database
        ;;
    "reset")
        reset_database
        if [ $? -eq 0 ]; then
            echo ""
            read -p "Load dummy data? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                seed_database
            fi
        fi
        ;;
    "seed")
        seed_database
        ;;
    "backup")
        backup_database
        ;;
    "restore")
        restore_database
        ;;
    "status")
        show_status
        ;;
    "test")
        test_database
        ;;
    "help"|*)
        show_help
        ;;
esac

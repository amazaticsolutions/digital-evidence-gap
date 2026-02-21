#!/bin/bash
# MongoDB initialization script

echo "Initializing MongoDB database..."

# Create the application database
mongosh --eval "use digital_evidence_gap"

# Create indexes (this will be run by the create_indexes.py script after deployment)
echo "MongoDB initialization complete."

# Create application user if credentials are provided
if [ -n "$MONGO_USERNAME" ] && [ -n "$MONGO_PASSWORD" ]; then
    mongosh digital_evidence_gap --eval "
        db.createUser({
            user: '$MONGO_USERNAME',
            pwd: '$MONGO_PASSWORD',
            roles: [
                {
                    role: 'readWrite',
                    db: 'digital_evidence_gap'
                }
            ]
        })
    "
    echo "Created application user: $MONGO_USERNAME"
fi
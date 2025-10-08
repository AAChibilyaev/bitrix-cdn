#!/bin/bash
# SSHFS mount script for Docker

set -e

# Configuration from environment
REMOTE_HOST=${REMOTE_HOST:-bitrix-server}
REMOTE_USER=${REMOTE_USER:-www-data}
REMOTE_PATH=${REMOTE_PATH:-/var/www/bitrix/upload}
MOUNT_POINT=${MOUNT_POINT:-/mnt/bitrix}
SSH_KEY=${SSH_KEY:-/root/.ssh/bitrix_mount}

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/sshfs/mount.log
}

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    log "ERROR: SSH key not found at $SSH_KEY"
    exit 1
fi

# Set proper permissions
chmod 600 "$SSH_KEY"

# Test SSH connection
log "Testing SSH connection to $REMOTE_USER@$REMOTE_HOST..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no \
    -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH OK'" | grep -q "SSH OK"; then
    log "SSH connection successful"
else
    log "ERROR: Cannot connect to remote server"
    exit 1
fi

# Unmount if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    log "Unmounting existing mount..."
    fusermount -u "$MOUNT_POINT" || true
    sleep 2
fi

# Create mount point
mkdir -p "$MOUNT_POINT"

# Mount with optimal parameters
log "Mounting $REMOTE_HOST:$REMOTE_PATH to $MOUNT_POINT..."

sshfs \
    -o allow_other \
    -o default_permissions \
    -o ro \
    -o cache=yes \
    -o kernel_cache \
    -o compression=no \
    -o ServerAliveInterval=15 \
    -o ServerAliveCountMax=3 \
    -o reconnect \
    -o auto_unmount \
    -o IdentityFile="$SSH_KEY" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -f \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH" "$MOUNT_POINT"

# Note: -f flag keeps sshfs in foreground for supervisor

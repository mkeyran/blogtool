# Hugo Blog Management Console

A Qt-based desktop application for managing Hugo blogs with multilingual support. This tool provides a convenient GUI interface for the most common blog management operations, replacing manual script execution with an intuitive workflow.

## Project Vision

A streamlined convenience tool focused on daily blog management operations rather than a full-featured CMS. The goal is to simplify the most common tasks while maintaining the flexibility of Hugo's file-based approach.

## Core Features

### Content Management

#### Post Creator
- Title/slug input with preview
- Language selection (Russian as default, auto-create translations)
- Category/tag picker
- Creates post structure via Hugo CLI integration

#### Micropost Creator
- Quick title/content input
- Auto-generated slug option
- One-click creation workflow

#### Conversation Creator
- Similar to posts but uses conversation archetype
- Optimized for dialogue/interview content

### Content Browser/Manager

#### Simple Tree View
- Organized by content type (Posts/Microposts/Conversations)
- Grouped by language
- Shows draft vs published status

#### Basic Operations
- Delete posts with confirmation
- Change status (draft ↔ published)
- "Open in Editor" button (configurable editor)
- "Open Folder" button (opens post directory in file manager)

### Publishing Pipeline

#### Draft → Published Workflow
- Move content between draft/published folders
- Update front matter automatically
- Simple status tracking and validation

### Site Operations

#### Hugo Server Controls
- Start/Stop/Restart Hugo development server
- Display server status and local URL
- Quick access to preview site

#### Git Operations
- Commit changes with custom messages
- Push to remote repository
- Basic git status display
- Commit message templates

### Configuration

#### Settings Panel
- Configurable external editor (VS Code, vim, etc.)
- Git commit message templates
- Default language preferences
- Hugo site path configuration

## Technical Architecture

- **Framework**: Qt6/PySide6 for cross-platform desktop application
- **Hugo Integration**: CLI subprocess calls for content creation and server management
- **Git Integration**: Subprocess-based git operations
- **File Management**: Native file system operations with OS integration

## Scope Limitations

This tool intentionally excludes:
- Built-in markdown editor (use external editor instead)
- Live preview within app (use Hugo server + browser)
- Media management (use file manager integration)
- Complex deployment automation (focus on git operations)
- Batch operations and advanced templating
- Content backup systems

## Target Workflow

1. Create new content via GUI forms
2. Open content in preferred external editor
3. Preview changes via Hugo server
4. Manage content status and organization
5. Commit and push changes via integrated git operations

This workflow balances convenience with simplicity, avoiding the complexity of a full CMS while streamlining daily blog management tasks.
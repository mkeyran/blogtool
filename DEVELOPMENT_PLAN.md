# Development Plan - Hugo Blog Management Console

This document outlines the iterative development approach for building the Qt-based Hugo blog management console.

## Overview

The project follows an MVP approach with 7 phases, prioritizing the most common daily workflow: microposts + git operations.

## Phase 1: Basic GUI + Micropost Creator (Playable MVP) ✅ COMPLETED
**Goal**: Get working Qt window with micropost functionality (quickest value)

### 1.1 Minimal Qt Application ✅
- [x] Create basic QMainWindow with menu bar
- [x] Add "About" dialog showing app info  
- [x] Test: Window opens and closes properly

### 1.2 Micropost Creator (MVP) ✅
- [x] Add "New Micropost" button/menu item
- [x] Create simple dialog: title input (optional) + auto-slug generation
- [x] Implement Hugo CLI integration (`hugo new content microposts/...`)
- [x] Test: Can create a real Hugo micropost file
- [x] Add success/error notifications

**Deliverable**: ✅ Working app that creates microposts via GUI (highest frequency use case)

**Implementation Details**:
- `MainWindow` class with File and Help menus
- "New Micropost" menu item with Ctrl+M shortcut  
- `MicropostDialog` with title input and filename preview
- `HugoManager` for Hugo CLI integration
- Comprehensive test coverage including real Hugo integration
- Creates microposts in correct `content/microposts/` directory

## Phase 2: Git Operations ✅ COMPLETED
**Goal**: Add version control workflow (second most important)

### 2.1 Basic Git Status ✅
- [x] Show git status in status bar or simple panel
- [x] Display modified files count
- [x] Test: Reflects actual git state

### 2.2 Commit & Push Workflow ✅
- [x] Add commit dialog with message input
- [x] Implement commit + push in one action
- [x] Add commit message templates for blog posts
- [x] Test: Creates real git commits and pushes

**Deliverable**: ✅ Complete micropost → git workflow (write and publish)

**Implementation Details**:
- `GitManager` class for git operations with status tracking
- Status bar shows current branch, file change counts, and unpushed commits
- `CommitDialog` with predefined templates for common blog operations
- One-click commit and push functionality in File menu (Ctrl+Shift+C)
- Comprehensive test coverage including unit tests and integration tests
- Real-time git status updates and automatic refresh after operations

## Phase 3: Content Browser Basics ✅ COMPLETED
**Goal**: Add ability to see and manage existing content

### 3.1 Simple Micropost Browser ✅
- [x] Add list widget showing microposts (title, date)
- [x] Display basic info from front matter
- [x] Test: Shows actual Hugo micropost files

### 3.2 Basic Actions ✅
- [x] "Open in Editor" button (configurable editor path)
- [x] "Open Folder" button (system file manager)
- [x] Delete micropost action
- [x] Test: All actions work with real files

**Deliverable**: ✅ Browse and manage existing microposts

**Implementation Details**:
- `MicropostBrowser` widget with custom `MicropostItem` display components
- `HugoManager.list_microposts()` method for parsing and listing microposts
- Smart title generation from content first line or filename fallback
- Preview generation with markdown formatting removal
- Multi-editor support with fallback error handling for "Open in Editor"
- Cross-platform file manager integration for "Open Folder"
- Confirmation dialogs and error handling for delete operations
- Comprehensive test coverage including unit tests and Qt widget testing
- Integration into main window with automatic refresh after operations

## Phase 4: Full Post Support
**Goal**: Extend to regular posts and conversations

### 4.1 Post Creator
- [ ] Add "New Post" dialog with title + language dropdown
- [ ] Multi-language post creation (Russian default + translations)
- [ ] Test: Creates real Hugo post structure

### 4.2 Conversation Creator
- [ ] Add conversation creation dialog
- [ ] Use conversation archetype
- [ ] Test: Creates conversation files

### 4.3 Extended Browser
- [ ] Show posts/conversations in browser tree
- [ ] Organize by content type
- [ ] Test: Shows all content types

**Deliverable**: Complete content creation and management

## Phase 5: Hugo Server Integration ✅ COMPLETED
**Goal**: Add preview capabilities

### 5.1 Server Controls ✅
- [x] Add Start/Stop/Restart Hugo server buttons
- [x] Show server status (running/stopped + URL)
- [x] Basic process management
- [x] Test: Server starts and stops correctly

### 5.2 Preview Integration ✅
- [x] "Preview Site" button (opens browser to localhost)
- [ ] Server output log viewer (optional)
- [x] Test: Preview works with live site

**Deliverable**: ✅ Integrated Hugo server management

**Implementation Details**:
- `HugoServerManager` class for complete Hugo development server lifecycle management
- Server menu in main window with Start/Stop/Restart/Preview actions and keyboard shortcuts
- Real-time server status display in status bar showing running state and URL
- Intelligent preview functionality that offers to start server if not running
- Cross-platform browser integration for site preview
- Process cleanup on application exit to prevent orphaned Hugo processes
- Comprehensive test coverage with 43 new tests covering server functionality and UI integration
- Full error handling with user-friendly messages for common issues

## Phase 6: Publishing Pipeline
**Goal**: Draft ↔ Published workflow

### 6.1 Status Management
- [ ] Show draft/published status in browser
- [ ] Add "Publish" and "Unpublish" actions
- [ ] Test: Actually moves files and updates front matter

### 6.2 Workflow Integration
- [ ] Combine publish + git commit actions
- [ ] Batch operations for multiple items
- [ ] Test: Full publish → commit → push workflow

**Deliverable**: Complete content lifecycle management

## Phase 7: Polish & Settings
**Goal**: Configuration and user experience improvements

### 7.1 Settings System
- [ ] Settings dialog for editor path, git templates, blog path
- [ ] Persistent configuration storage
- [ ] Test: Settings persist between sessions

### 7.2 UI Polish
- [ ] Keyboard shortcuts (Ctrl+M for new micropost)
- [ ] Better icons and styling
- [ ] Error handling improvements
- [ ] Recent microposts quick access
- [ ] Test: Smooth user experience

**Deliverable**: Production-ready application

## Development Strategy

### Key Principles
- **Each Phase Delivers Working Software**: Every phase adds one complete, testable feature
- **Early Value**: After Phase 1, you have a functional micropost creator
- **Iterative Feedback**: Can stop at any phase and still have value
- **Real Integration**: Test with actual Hugo content throughout

### Phase Rationale
1. **Microposts First**: Highest frequency use case, simplest to implement, immediate value
2. **Git Operations Next**: Essential for publishing workflow, completes the write→publish cycle  
3. **Content Browser**: Management of existing content
4. **Full Posts**: More complex multi-language features
5. **Hugo Server**: Preview functionality
6. **Publishing Pipeline**: Advanced workflow features
7. **Polish**: User experience improvements

This prioritizes the most common daily workflow: write micropost → commit → push.

## Success Metrics

### Phase 1 Success
- Can create microposts faster than manual process
- Generated files are properly formatted Hugo content
- No crashes or data loss

### Phase 2 Success  
- Git operations are reliable and atomic
- Commit messages are meaningful and consistent
- Push operations handle common error cases

### Overall Success
- Tool saves time compared to manual Hugo + git workflow
- Reduces context switching between terminal and editor
- Provides confidence in content publishing process
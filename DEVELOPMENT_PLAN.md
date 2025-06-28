# Development Plan - Hugo Blog Management Console

This document outlines the iterative development approach for building the Qt-based Hugo blog management console.

## Overview

The project follows an MVP approach with 7 phases, prioritizing the most common daily workflow: microposts + git operations.

## Phase 1: Basic GUI + Micropost Creator (Playable MVP)
**Goal**: Get working Qt window with micropost functionality (quickest value)

### 1.1 Minimal Qt Application
- [ ] Create basic QMainWindow with menu bar
- [ ] Add "About" dialog showing app info  
- [ ] Test: Window opens and closes properly

### 1.2 Micropost Creator (MVP)
- [ ] Add "New Micropost" button/menu item
- [ ] Create simple dialog: title input (optional) + auto-slug generation
- [ ] Implement Hugo CLI integration (`hugo new content microposts/...`)
- [ ] Test: Can create a real Hugo micropost file
- [ ] Add success/error notifications

**Deliverable**: Working app that creates microposts via GUI (highest frequency use case)

## Phase 2: Git Operations
**Goal**: Add version control workflow (second most important)

### 2.1 Basic Git Status
- [ ] Show git status in status bar or simple panel
- [ ] Display modified files count
- [ ] Test: Reflects actual git state

### 2.2 Commit & Push Workflow
- [ ] Add commit dialog with message input
- [ ] Implement commit + push in one action
- [ ] Add commit message templates for blog posts
- [ ] Test: Creates real git commits and pushes

**Deliverable**: Complete micropost → git workflow (write and publish)

## Phase 3: Content Browser Basics
**Goal**: Add ability to see and manage existing content

### 3.1 Simple Micropost Browser
- [ ] Add list widget showing microposts (title, date)
- [ ] Display basic info from front matter
- [ ] Test: Shows actual Hugo micropost files

### 3.2 Basic Actions
- [ ] "Open in Editor" button (configurable editor path)
- [ ] "Open Folder" button (system file manager)
- [ ] Delete micropost action
- [ ] Test: All actions work with real files

**Deliverable**: Browse and manage existing microposts

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

## Phase 5: Hugo Server Integration
**Goal**: Add preview capabilities

### 5.1 Server Controls
- [ ] Add Start/Stop/Restart Hugo server buttons
- [ ] Show server status (running/stopped + URL)
- [ ] Basic process management
- [ ] Test: Server starts and stops correctly

### 5.2 Preview Integration
- [ ] "Preview Site" button (opens browser to localhost)
- [ ] Server output log viewer (optional)
- [ ] Test: Preview works with live site

**Deliverable**: Integrated Hugo server management

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
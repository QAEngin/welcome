# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HOT Business Welcome Page - A Hebrew-language static website providing service guides and documentation for HOT Business telephony services. The site serves as a central hub for customers to access guides for fax services, SMS, call recordings, and Yealink phone systems.

## Architecture

### Core Structure
- **index.html**: Main Hebrew RTL page with service guide cards
- **app.js**: Core functionality for guide display, search, and navigation
- **style.css**: Dark-themed responsive styling with Hebrew RTL support
- **admin.html / admin.js**: Content management interface using localStorage

### Key Features
- **Guide System**: Interactive cards that expand to show detailed guides
- **Search**: Real-time filtering of guide cards
- **Admin Panel**: Simple editor for modifying guide content
- **PDF Integration**: Uses PDF.js for embedded document viewing
- **Video Guides**: MP4 video tutorials for phone system usage

### Content Organization
- **guides/**: PDF manuals and video tutorials
  - `manual-centrix.pdf`: Main Yealink user manual
  - `video/`: Video tutorials (BLF setup, conference calls)
- **assets/**: Images (logo.png, Rec.png)

## Development

### Running Locally
```bash
# Serve files using any static server
python -m http.server 8000
# or
npx serve .
# or
live-server
```

### File Serving Requirements
- Static file server needed for proper PDF.js functionality
- No build process required - direct file serving

### Testing
- Test all guide expansions and search functionality
- Verify Hebrew RTL rendering across browsers
- Test admin panel guide editing and localStorage persistence
- Ensure PDF viewing works properly
- Verify video playback in guide sections

## Key Implementation Details

### Guide Management
- Guide content stored as template literals in `app.js`
- Admin panel uses localStorage for content overrides
- Search filters cards based on visible text content

### Hebrew/RTL Support
- HTML uses `lang="he" dir="rtl"`
- CSS designed for right-to-left layout
- Font Awesome icons for UI elements

### External Dependencies
- Font Awesome 6.5.1 (CDN)
- PDF.js 2.16.105 (CDN)
- No package manager or build tools

### Responsive Design
- Mobile-first approach with CSS Grid/Flexbox
- Sticky navigation with dynamic offset calculation
- Responsive video and PDF viewing

## Content Guidelines

### Adding New Guides
1. Add new guide object to `guides` in app.js
2. Create corresponding card in index.html features section
3. Ensure onclick calls `toggleGuide('new-guide-name')`
4. Test search functionality includes new content

### Guide Content Structure
- Use `.guide-box` wrapper for consistent styling
- Structure with h2/h3 headings and ordered lists
- Include PDF preview buttons where applicable
- Maintain Hebrew RTL text direction

### Admin Panel Usage
- Access via `admin.html`
- Select guide type from dropdown
- Edit content in textarea
- Save changes to localStorage (overrides default content)

## External Resources

### Service Links
- WhatsApp Support: https://wa.me/972778066666
- Call Recordings System: https://hot.nimbusip.com/

### Content Assets
- PDF guides should be placed in `guides/` directory
- Videos should be in `guides/video/` with MP4 format
- Images in `assets/` directory

## Browser Compatibility

- Modern browsers supporting ES6+ features
- PDF.js requires browsers with native PDF support fallback
- Video guides require MP4 codec support
- Font Awesome requires modern CSS support
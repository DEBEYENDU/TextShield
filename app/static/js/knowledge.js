/* TextShield Knowledge JavaScript - Knowledge Explorer Page */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize knowledge explorer on load
    initKnowledgeExplorer();
    
    // Initialize search functionality
    initKnowledgeSearch();
});

/* Initialize knowledge explorer */
function initKnowledgeExplorer() {
    // Fetch categories, tags, articles, glossary via AJAX
    fetchKnowledgeData();
}

/* Fetch all knowledge data */
function fetchKnowledgeData() {
    // Fetch categories
    fetch('/api/knowledge/categories')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayCategories(data.data);
            }
        })
        .catch(error => console.error('Failed to fetch categories:', error));
    
    // Fetch tags
    fetch('/api/knowledge/tags')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTags(data.data);
            }
        })
        .catch(error => console.error('Failed to fetch tags:', error));
    
    // Fetch articles
    fetch('/api/knowledge/articles')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayArticles(data.data);
            }
        })
        .catch(error => console.error('Failed to fetch articles:', error));
    
    // Fetch glossary
    fetch('/api/knowledge/glossary')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayGlossary(data.data);
            }
        })
        .catch(error => console.error('Failed to fetch glossary:', error));
}

/* Display categories */
function displayCategories(categories) const kbGrid = document.getElementById('kb-grid');
    if (!kbGrid) return;
    
    kbGrid.innerHTML = '';
    
    categories.forEach(category => {
        const div = document.createElement('div');
        div.className = 'chip';
        div.title = category;
        div.innerText = category;
        div.style.cursor = 'pointer';
        div.style.fontSize = '0.875rem';
        div.style.padding = '0.5rem 0.75rem';
        div.style.borderRadius = '4px';
        div.style.margin = '0.2rem';
        div.style.background = 'var(--primary-light)';
        div.style.color = 'var(--text-primary)';
        
        div.addEventListener('click', function() {
            // Navigate to articles in this category
            console.log('Category clicked:', category);
        });
        
        kbGrid.appendChild(div);
    });
}

/* Display tags */
function displayTags(tags) {
    const tagCloud = document.getElementById('tag-cloud');
    if (!tagCloud) return;
    
    tagCloud.innerHTML = '';
    
    tags.forEach(tag => {
        const span = document.createElement('span');
        span.className = 'chip';
        span.title = tag;
        span.innerText = tag;
        span.style.fontSize = '0.75rem';
        span.style.padding = '0.25rem 0.5rem';
        span.style.margin = '0.1rem';
        span.style.background = 'var(--primary-light)';
        span.style.color = 'var(--text-primary)';
        span.style.cursor = 'pointer';
        
        span.addEventListener('click', function() {
            // Filter articles by tag
            console.log('Tag clicked:', tag);
        });
        
        tagCloud.appendChild(span);
    });
}

/* Display articles */
function displayArticles(articles) {
    const articleList = document.getElementById('article-list');
    if (!articleList) return;
    
    articleList.innerHTML = '';
    
    articles.forEach(article => {
        const div = document.createElement('div');
        div.className = 'mb-2';
        div.style.padding = '0.5rem';
        div.style.borderBottom = '1px solid var(--border)';
        
        div.innerHTML = `
            <h6 class="mb-1">${article.title || 'Untitled'}</h6>
            <small class="text-secondary">${article.category || 'Uncategorized'}</small>
            <p class="mb-0 small">${article.content ? article.content.substring(0, 100) + '...' : 'No content'}...</p>
        `;
        
        articleList.appendChild(div);
    });
}

/* Display glossary */
function displayGlossary(entries) {
    const glossaryList = document.getElementById('glossary-list');
    if (!glossaryList) return;
    
    glossaryList.innerHTML = '';
    
    entries.forEach(entry => {
        const div = document.createElement('div');
        div.className = 'mb-2';
        div.style.padding = '0.5rem';
        div.style.borderBottom = '1px solid var(--border)';
        
        div.innerHTML = `
            <strong>${entry.term}</strong>: ${entry.definition || 'No definition available'}
        `;
        
        glossaryList.appendChild(div);
    });
}

/* Initialize search functionality */
function initKnowledgeSearch() {
    const searchInputs = document.querySelectorAll('#kb-search, #tag-search, #article-search, #glossary-search');
    
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const query = this.value.toLowerCase();
            const targetId = this.id.replace('search', '');
            const items = document.querySelectorAll(`#${targetId} .chip, #${targetId} .article-list div, #${targetId} .glossary-list div`);
            
            items.forEach(item => {
                const text = item.innerText.toLowerCase();
                item.style.display = text.includes(query) ? 'block' : 'none';
            });
        });
    });
}
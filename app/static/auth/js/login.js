const quotes = [
    { text: "Stay hungry, stay foolish.", author: "Steve Jobs", role: "Co-Founder, Apple" },
    { text: "Talk is cheap. Show me the code.", author: "Linus Torvalds", role: "Creator of Linux" },
    { text: "Software is eating the world.", author: "Marc Andreessen", role: "Co-author of Mosaic" },
    { text: "The people who are crazy enough to think they can change the world are the ones who do.", author: "Rob Siltanen", role: "Apple 'Think Different'" },
    { text: "Move fast and break things.", author: "Mark Zuckerberg", role: "Founder, Facebook" },
    { text: "Computers are incredibly fast, accurate, and stupid. Human beings are incredibly slow, inaccurate, and brilliant.", author: "Albert Einstein", role: "Physicist" },
    { text: "First, solve the problem. Then, write the code.", author: "John Johnson", role: "Developer" },
    { text: "It’s not a bug – it’s an undocumented feature.", author: "Anonymous", role: "Developer Folklore" },
    { text: "Java is to JavaScript what car is to Carpet.", author: "Chris Heilmann", role: "Developer" },
    { text: "Code is like humor. When you have to explain it, it’s bad.", author: "Cory House", role: "Clean Code Advocate" }
];

let currentIdx = 0;
const slideDuration = 6000;

function initCarousel() {
    const textEl = document.getElementById('quote-text');
    const authorEl = document.getElementById('quote-author');
    const roleEl = document.getElementById('quote-role');
    const container = document.querySelector('.carousel-container');
    const content = document.querySelector('.carousel-content');

    function showSlide(index) {
        // 1. Lock current height so it doesn't snap
        const startHeight = container.offsetHeight;
        container.style.height = startHeight + 'px';

        // 2. Fade Out Text
        content.style.opacity = '0';
        content.style.transform = 'translateY(10px)';

        setTimeout(() => {
            // 3. Update Text (While hidden)
            const q = quotes[index];
            textEl.textContent = `“${q.text}”`;
            authorEl.textContent = q.author;
            roleEl.textContent = q.role;

            // 4. Update Dots
            document.querySelectorAll('.dot').forEach((d, i) => {
                d.classList.toggle('active', i === index % 3);
            });

            // 5. Calculate New Height (The Magic Trick)
            // We temporarily let it grow to 'auto' to see how big it WANTS to be
            container.style.height = 'auto';
            const targetHeight = container.offsetHeight; // Measure it
            
            // Immediately snap back to startHeight so we can animate from there
            container.style.height = startHeight + 'px';
            
            // Force browser to realize we snapped back (Reflow)
            void container.offsetHeight; 

            // 6. Animate to the new Target Height
            container.style.height = targetHeight + 'px';

            // 7. Fade In Text
            content.style.opacity = '1';
            content.style.transform = 'translateY(0)';

        }, 400); // Wait for fade out
    }

    // Auto Player
    setInterval(() => {
        currentIdx = (currentIdx + 1) % quotes.length;
        showSlide(currentIdx);
    }, slideDuration);

    // Initial Render
    showSlide(0);
    
    // Safety: Set height to auto after transition so window resizing works
    container.addEventListener('transitionend', () => {
        container.style.height = 'auto';
    });
}

document.addEventListener('DOMContentLoaded', initCarousel);
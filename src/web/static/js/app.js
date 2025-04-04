/**
 * Main JavaScript file for the Privacy-Preserving Emotion Analysis application
 */

// Chart objects to manage the visualizations
let emotionChart = null;
let emotionRadarChart = null;
let emotionBreakdownChart = null;

$(document).ready(function() {
    // Form submission
    $('#sentimentForm').on('submit', function(e) {
        e.preventDefault();

        // Show loader and start progress animation
        $('#loader').show();

        // Animate the FHE progress bar
        let progressValue = 0;
        const progressInterval = setInterval(function() {
            progressValue += 5;
            if (progressValue <= 95) {
                $('#fheProgress').css('width', progressValue + '%').attr('aria-valuenow', progressValue).text(progressValue + '%');
            }
        }, 1000);

        // Hide results if previously shown
        $('#results').hide();

        // Get form data
        const formData = {
            question: $('#question').val(),
            username: $('#username').val(),
            password: $('#password').val()
        };

        // Send AJAX request
        $.ajax({
            url: '/analyze',
            type: 'POST',
            data: formData,
            success: function(response) {
                // Hide loader and stop progress animation
                clearInterval(progressInterval);
                $('#fheProgress').css('width', '100%').attr('aria-valuenow', 100).text('100%');
                setTimeout(function() {
                    $('#loader').hide();
                }, 500);

                // Update results
                $('#result-question').text(response.question);
                $('#result-post-count').text(response.post_count);

                // Update emotion with appropriate styling
                const overallEmotion = response.overall_emotion;
                $('#result-overall-emotion').text(overallEmotion)
                    .css('color', getEmotionColor(overallEmotion));

                // Create interactive charts
                createEmotionDonutChart('emotionChart', response);
                createEmotionRadarChart('emotionRadarChart', response);
                createEmotionBreakdownChart('emotionBreakdownChart', response);

                // Add sample posts
                const samplePostsContainer = $('#sample-posts');
                samplePostsContainer.empty();

                // Only display first 5 posts in UI for performance, though we analyze 50
                const displayPosts = response.sample_posts.slice(0, 5);
                const totalPosts = response.sample_posts.length;

                displayPosts.forEach(function(post, index) {
                    const displayText = post.length > 150 ? post.substring(0, 150) + '...' : post;
                    const emotionData = response.emotions_data[index] || { dominant_emotion: 'neutral' };
                    const emotionColor = getEmotionColor(emotionData.dominant_emotion);

                    samplePostsContainer.append(`
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">Post ${index + 1} of ${totalPosts}</small>
                                <span class="badge" style="background-color: ${emotionColor}">${emotionData.dominant_emotion}</span>
                            </div>
                            <p class="mb-1">${displayText}</p>
                        </div>
                    `);
                });

                // Add a message showing we're analyzing more posts than displaying
                if (totalPosts > 5) {
                    samplePostsContainer.append(`
                        <div class="list-group-item text-center bg-light">
                            <small class="text-muted">+ ${totalPosts - 5} more posts analyzed (not displayed)</small>
                        </div>
                    `);
                }

                // Show results
                $('#results').show();

                // Update FHE info if available
                if (response.fhe_enabled && response.fhe_details) {
                    const fheDetails = `<div class="mt-2 small">
                        <strong>FHE Method:</strong> ${response.fhe_details.method}<br>
                        <strong>Description:</strong> ${response.fhe_details.description}
                    </div>`;
                    $('#fheInfo p').append(fheDetails);
                }

                // Scroll to results
                $('html, body').animate({
                    scrollTop: $("#results").offset().top - 100
                }, 500);
            },
            error: function(xhr) {
                // Hide loader and stop progress animation
                clearInterval(progressInterval);
                $('#loader').hide();

                // Show error
                let errorMessage = 'An error occurred during the analysis.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }

                alert(errorMessage);
            }
        });
    });

    // FHE information is now displayed automatically as part of the main analysis

    // Test authentication button
    $('#testAuth').on('click', function() {
        const username = $('#username').val();
        const password = $('#password').val();

        if (!username || !password) {
            alert("Please enter both username and password to test authentication");
            return;
        }

        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status"></span> Testing...');

        $.ajax({
            url: '/test_auth',
            type: 'POST',
            data: {
                username: username,
                password: password
            },
            success: function(response) {
                alert("Authentication successful! You can now analyze posts.");
                $('#testAuth').prop('disabled', false).html('Test Authentication');
            },
            error: function(xhr) {
                let message = "Authentication failed. Please check your credentials.";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    message = xhr.responseJSON.error;
                }
                alert(message);
                $('#testAuth').prop('disabled', false).html('Test Authentication');
            }
        });
    });
});

/**
 * Get color for a specific emotion
 */
function getEmotionColor(emotion) {
    const colors = {
        'joy': '#FFD700',      // Gold
        'surprise': '#FF8C00', // Dark Orange
        'neutral': '#A9A9A9',  // Dark Gray
        'sadness': '#1E90FF',  // Dodger Blue
        'fear': '#800080',     // Purple
        'anger': '#FF0000',    // Red
        'disgust': '#006400',  // Dark Green
    };

    return colors[emotion] || '#A9A9A9';
}

/**
 * Create interactive donut chart for emotion distribution
 */
function createEmotionDonutChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Destroy existing chart if it exists
    if (emotionChart) {
        emotionChart.destroy();
    }

    // Get the emotion data
    const labels = Object.keys(data.emotion_counts);
    const counts = Object.values(data.emotion_counts);
    const colors = data.colors || labels.map(getEmotionColor);

    // Create the chart
    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: colors,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} posts (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true
            },
            onClick: function(event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    alert(`${labels[index]}: ${counts[index]} posts`);
                }
            }
        }
    });
}

/**
 * Create interactive radar chart for emotion intensity
 */
function createEmotionRadarChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Destroy existing chart if it exists
    if (emotionRadarChart) {
        emotionRadarChart.destroy();
    }

    // Get the emotion data
    const labels = Object.keys(data.emotion_scores);
    const scores = Object.values(data.emotion_scores);
    const colors = data.colors || labels.map(getEmotionColor);

    // Create the chart
    emotionRadarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Emotion Intensity',
                data: scores,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                pointBackgroundColor: colors,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: colors
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        stepSize: 0.2
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${(context.raw * 100).toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create interactive bar chart for emotion breakdown by post
 */
function createEmotionBreakdownChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Destroy existing chart if it exists
    if (emotionBreakdownChart) {
        emotionBreakdownChart.destroy();
    }

    // Only show up to 10 posts for chart clarity, even though we're analyzing 50
    const emotionsData = data.emotions_data.slice(0, 10);

    // Prepare data for stacked bar chart
    const emotions = Object.keys(data.emotion_scores);
    const datasets = emotions.map((emotion, index) => {
        return {
            label: emotion,
            data: emotionsData.map(item => item.emotions[emotion]),
            backgroundColor: getEmotionColor(emotion)
        };
    });

    // Create the chart
    emotionBreakdownChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: emotionsData.map((_, index) => `Post ${index + 1}`),
            datasets: datasets
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    max: 1
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${(value * 100).toFixed(1)}%`;
                        }
                    }
                }
            },
            onClick: function(event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    // Show the post text in a modal or alert
                    if (index < data.sample_posts.length) {
                        alert(data.sample_posts[index]);
                    }
                }
            }
        }
    });
}

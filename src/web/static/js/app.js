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
        
        // Show loader
        $('#loader').show();
        
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
                // Hide loader
                $('#loader').hide();
                
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
                
                response.sample_posts.forEach(function(post, index) {
                    const displayText = post.length > 150 ? post.substring(0, 150) + '...' : post;
                    const emotionData = response.emotions_data[index] || { dominant_emotion: 'neutral' };
                    const emotionColor = getEmotionColor(emotionData.dominant_emotion);
                    
                    samplePostsContainer.append(`
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">Post ${index + 1}</small>
                                <span class="badge" style="background-color: ${emotionColor}">${emotionData.dominant_emotion}</span>
                            </div>
                            <p class="mb-1">${displayText}</p>
                        </div>
                    `);
                });
                
                // Show results
                $('#results').show();
                
                // Scroll to results
                $('html, body').animate({
                    scrollTop: $("#results").offset().top - 100
                }, 500);
            },
            error: function(xhr) {
                // Hide loader
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
    
    // Generate proof button
    $('#generateProofBtn').on('click', function() {
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...');
        
        $.ajax({
            url: '/generate_proof',
            type: 'POST',
            success: function(response) {
                $('#generateProofBtn').prop('disabled', false).html('<i class="fas fa-shield-alt me-2"></i>Generate Zero-Knowledge Proof');
                
                if (response.success) {
                    $('#zkProofMessage').text(response.verification);
                    $('#zkProofResult').removeClass('alert-danger').addClass('alert-info').slideDown();
                } else {
                    $('#zkProofMessage').text(response.message);
                    $('#zkProofResult').removeClass('alert-info').addClass('alert-danger').slideDown();
                }
            },
            error: function() {
                $('#generateProofBtn').prop('disabled', false).html('<i class="fas fa-shield-alt me-2"></i>Generate Zero-Knowledge Proof');
                $('#zkProofMessage').text('Failed to generate proof. Please try again.');
                $('#zkProofResult').removeClass('alert-info').addClass('alert-danger').slideDown();
            }
        });
    });

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
    
    // Only show up to 5 posts for clarity
    const emotionsData = data.emotions_data.slice(0, 5);
    
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

# Use Nginx Alpine as base image
FROM nginx:alpine

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create directory for static files
RUN mkdir -p /usr/share/nginx/html/static

# Copy static files
COPY static/css/ /usr/share/nginx/html/static/css/
COPY static/js/ /usr/share/nginx/html/static/js/

# Copy index.html
COPY templates/index.html /usr/share/nginx/html/index.html

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 
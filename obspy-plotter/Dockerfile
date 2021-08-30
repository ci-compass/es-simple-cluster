FROM python:3

# Create a non-root user for runtime operations inside the container 
RUN useradd -ms /bin/bash plotter
WORKDIR /home/plotter

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy files
COPY . .

# Ensure the user owns everything in its area
RUN chown -R plotter:plotter *

# Perform operations with the user
USER plotter

ENV FLASK_APP=plotter
ENV FLASK_ENV=development
CMD ["flask", "run", "--host=0.0.0.0"]
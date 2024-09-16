pub:
	podman rm -f tess
	podman build -t tess:latest .
	podman run -d -p 8502:8501 --name tess localhost/tess:latest 
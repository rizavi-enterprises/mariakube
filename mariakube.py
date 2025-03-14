# MariaKube can be deployed by:
# 1. Cloning the Mariakube GitHub repo, and running the commands in the README file. 
# OR
# 2. Running this script.

import os
import subprocess

def run_command(command):
    """Run a shell command and print its output."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error: {stderr.decode('utf-8')}")
        exit(1)
    print(stdout.decode('utf-8'))

def create_file(file_path, content):
    """Create a file with the given content."""
    with open(file_path, 'w') as file:
        file.write(content)
    print(f"Created file: {file_path}")

def main():
    # Step 1: Install K3s
    print("Installing K3s...")
    run_command("curl -sfL https://get.k3s.io | sh -")

    # Step 2: Set up kubectl access for the current user
    print("Setting up kubectl access...")
    run_command("mkdir -p ~/.kube")
    run_command("sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config")
    run_command("sudo chown $(id -u):$(id -g) ~/.kube/config")
    run_command("export KUBECONFIG=~/.kube/config")

    # Step 3: Install KubeSphere
    print("Installing KubeSphere...")
    run_command("kubectl apply -f https://github.com/kubesphere/ks-installer/releases/download/v3.3.2/kubesphere-installer.yaml")
    run_command("kubectl apply -f https://github.com/kubesphere/ks-installer/releases/download/v3.3.2/cluster-configuration.yaml")

    # Step 4: Create a namespace for MariaDB
    print("Creating namespace for MariaDB...")
    run_command("kubectl create namespace mariadb")

    # Step 5: Create PVC for MariaDB
    print("Creating PVC for MariaDB...")
    pvc_content = """
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mariadb-pvc
  namespace: mariadb
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
"""
    create_file("mariadb-pvc.yaml", pvc_content)
    run_command("kubectl apply -f mariadb-pvc.yaml")

    # Step 6: Deploy MariaDB
    print("Deploying MariaDB...")
    mariadb_deployment_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mariadb
  namespace: mariadb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mariadb
  template:
    metadata:
      labels:
        app: mariadb
    spec:
      containers:
      - name: mariadb
        image: mariadb:10.6
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "rootpassword"
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mariadb-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mariadb-storage
        persistentVolumeClaim:
          claimName: mariadb-pvc
"""
    create_file("mariadb-deployment.yaml", mariadb_deployment_content)
    run_command("kubectl apply -f mariadb-deployment.yaml")

    # Step 7: Expose MariaDB via a Service
    print("Exposing MariaDB via a Service...")
    mariadb_service_content = """
apiVersion: v1
kind: Service
metadata:
  name: mariadb-service
  namespace: mariadb
spec:
  selector:
    app: mariadb
  ports:
  - protocol: TCP
    port: 3306
    targetPort: 3306
"""
    create_file("mariadb-service.yaml", mariadb_service_content)
    run_command("kubectl apply -f mariadb-service.yaml")

    # Step 8: Verify the setup
    print("Verifying the setup...")
    run_command("kubectl get pvc -n mariadb")
    run_command("kubectl get pods -n mariadb")
    run_command("kubectl get svc -n mariadb")

    print("Setup complete! KubeSphere should be accessible at http://<VM-IP>:30880")

if __name__ == "__main__":
    main()

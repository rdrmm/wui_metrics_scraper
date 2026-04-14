# Define variables
$PrometheusVersion = "2.53.2"  # Update to the latest version from https://github.com/prometheus/prometheus/releases
$DownloadUrl = "https://github.com/prometheus/prometheus/releases/download/v$PrometheusVersion/prometheus-$PrometheusVersion.windows-amd64.zip"
$InstallDir = "C:\Program Files\Prometheus"
$NssmUrl = "https://nssm.cc/release/nssm-2.24.zip"  # NSSM version; check for updates
$TempDir = "$env:TEMP\prometheus_install"
$PrometheusExe = "$InstallDir\prometheus.exe"
$NssmExe = "$TempDir\nssm-2.24\win64\nssm.exe"

# Create temp directory
New-Item -ItemType Directory -Path $TempDir -Force

# Download Prometheus
Write-Host "Downloading Prometheus..."
Invoke-WebRequest -Uri $DownloadUrl -OutFile "$TempDir\prometheus.zip"

# Download NSSM
Write-Host "Downloading NSSM..."
Invoke-WebRequest -Uri $NssmUrl -OutFile "$TempDir\nssm.zip"

# Extract Prometheus
Write-Host "Extracting Prometheus..."
Expand-Archive -Path "$TempDir\prometheus.zip" -DestinationPath $TempDir
Move-Item -Path "$TempDir\prometheus-$PrometheusVersion.windows-amd64\*" -Destination $InstallDir -Force

# Extract NSSM
Write-Host "Extracting NSSM..."
Expand-Archive -Path "$TempDir\nssm.zip" -DestinationPath $TempDir

# Install Prometheus as a service using NSSM
Write-Host "Installing Prometheus as a service..."
& $NssmExe install Prometheus $PrometheusExe
& $NssmExe set Prometheus AppDirectory $InstallDir
& $NssmExe set Prometheus AppParameters "--config.file=$InstallDir\prometheus.yml --storage.tsdb.path=$InstallDir\data"
& $NssmExe set Prometheus Description "Prometheus monitoring system"
& $NssmExe set Prometheus Start SERVICE_AUTO_START

# Start the service
Write-Host "Starting Prometheus service..."
Start-Service -Name Prometheus

# Clean up
Remove-Item -Path $TempDir -Recurse -Force

Write-Host "Prometheus installed and started as a service."
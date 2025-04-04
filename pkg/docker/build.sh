#!/usr/bin/env bash

# Initialize publish flag
publish_build=false

gh_username="vkuusk"
docker_image_name="codemorf"

# Print help message
print_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  publish        Build and publish Docker image to GitHub Container Registry"
    echo
    echo "Examples:"
    echo "  $0              Build Docker image locally only"
    echo "  $0 publish      Build and publish Docker image to GitHub Container Registry"
}

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_help
            exit 0
            ;;
        publish)
            publish_build=true
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            print_help
            exit 1
            ;;
    esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

root_dir="${script_dir}/../.."

# build wheel file
pushd $root_dir > /dev/null

python3 -m build

wheel_file=(dist/*.whl)
cp "${wheel_file[0]}" "${script_dir}/"

# cleanup root_dir
rm -rf dist/ src/*.egg-info/

popd > /dev/null

# build Docker image
pushd $script_dir > /dev/null

# Build with both local and GitHub Container Registry tags if publishing
if [ "$publish_build" = true ]; then
    echo "Building with GitHub Container Registry tag..."
    docker build -t "${docker_image_name}:latest" -t "ghcr.io/${gh_username}/${docker_image_name}:latest" .
else
    echo "Building with local tag only..."
    docker build -t "${docker_image_name}:latest" .
fi

# Push to GitHub Container Registry if publishing
if [ "$publish_build" = true ]; then
    # Login to GitHub Container Registry
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "Error: GITHUB_TOKEN environment variable is not set"
        echo "Please set it with: export GITHUB_TOKEN=your_github_pat"
        exit 1
    fi

    echo "Logging in to GitHub Container Registry..."
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u ${gh_username} --password-stdin

    echo "Pushing image to GitHub Container Registry..."
    docker push "ghcr.io/${gh_username}/${docker_image_name}:latest"
fi

# Cleanup docker build dir
rm codemorf-*.whl

popd > /dev/null

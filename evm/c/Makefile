# EVM C Implementation Makefile
# Supports: macOS, Linux

CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c99 -D_GNU_SOURCE
LDFLAGS = 
TARGET = evm

# Source files
SOURCES = main.c core.c utils.c list.c io.c group.c
OBJECTS = $(SOURCES:.c=.o)

# Default target
all: $(TARGET)

# Build target
$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(TARGET) $(LDFLAGS)
	@echo "Build complete: $(TARGET)"

# Compile source files
%.o: %.c evm.h
	$(CC) $(CFLAGS) -c $< -o $@

# Clean build files
clean:
	rm -f $(OBJECTS) $(TARGET)
	rm -rf evm-cli-macos evm-cli-macos.tar.gz
	@echo "Clean complete"

# Install locally (development)
install-local: $(TARGET)
	cp $(TARGET) /usr/local/bin/
	chmod +x /usr/local/bin/$(TARGET)
	@echo "Installed to /usr/local/bin/$(TARGET)"

# Uninstall
uninstall:
	rm -f /usr/local/bin/$(TARGET)
	@echo "Uninstalled $(TARGET)"

# Copy to bin directory
install: $(TARGET)
	mkdir -p ../../bin
	cp $(TARGET) ../../bin/
	cp evm-cli-macos.tar.gz ../../bin/ 2>/dev/null || true
	@echo "Installed to ../../bin/"

# Create macOS distribution package
dist-macos: $(TARGET)
	@echo "Creating macOS distribution package..."
	mkdir -p evm-cli-macos
	cp $(TARGET) evm-cli-macos/
	cp ../../README.md evm-cli-macos/ 2>/dev/null || echo "README.md not found"
	cp ../../LICENSE evm-cli-macos/ 2>/dev/null || echo "LICENSE not found"
	
	@echo '#!/bin/bash' > evm-cli-macos/install.sh
	@echo '# EVM macOS Installation Script' >> evm-cli-macos/install.sh
	@echo 'set -e' >> evm-cli-macos/install.sh
	@echo '' >> evm-cli-macos/install.sh
	@echo 'echo "Installing EVM..."' >> evm-cli-macos/install.sh
	@echo 'INSTALL_DIR="/usr/local/bin"' >> evm-cli-macos/install.sh
	@echo '' >> evm-cli-macos/install.sh
	@echo 'if [[ ! -w "$$INSTALL_DIR" ]]; then' >> evm-cli-macos/install.sh
	@echo '    echo "需要管理员权限来安装到 $$INSTALL_DIR"' >> evm-cli-macos/install.sh
	@echo '    sudo cp evm "$$INSTALL_DIR/"' >> evm-cli-macos/install.sh
	@echo '    sudo chmod +x "$$INSTALL_DIR/evm"' >> evm-cli-macos/install.sh
	@echo 'else' >> evm-cli-macos/install.sh
	@echo '    cp evm "$$INSTALL_DIR/"' >> evm-cli-macos/install.sh
	@echo '    chmod +x "$$INSTALL_DIR/evm"' >> evm-cli-macos/install.sh
	@echo 'fi' >> evm-cli-macos/install.sh
	@echo '' >> evm-cli-macos/install.sh
	@echo 'echo "✓ EVM 安装成功!"' >> evm-cli-macos/install.sh
	@echo 'echo ""' >> evm-cli-macos/install.sh
	@echo 'echo "运行 'evm --help' 开始使用"' >> evm-cli-macos/install.sh
	
	chmod +x evm-cli-macos/install.sh
	chmod +x evm-cli-macos/$(TARGET)
	
	tar -czf evm-cli-macos.tar.gz evm-cli-macos
	@echo "Distribution package created: evm-cli-macos.tar.gz"

# Debug build
debug: CFLAGS = -Wall -Wextra -g -O0 -std=c99 -D_GNU_SOURCE
debug: clean $(TARGET)

# Run tests
test: $(TARGET)
	./$(TARGET) --version
	./$(TARGET) set TEST_VAR "hello world"
	./$(TARGET) get TEST_VAR
	./$(TARGET) list
	./$(TARGET) delete TEST_VAR
	@echo "Basic tests passed!"

.PHONY: all clean install install-local uninstall dist-macos debug test

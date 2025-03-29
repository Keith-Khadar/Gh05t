cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(tcpWebsocket_p C CXX ASM)
set(CMAKE_C STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

pico_sdk_init()

add_executable(tcpServer
	main.c
)

pico_enable_stdio_usb(tcpServer 1)
pico_enable_stdio_uart(tcpServer 0)

pico_add_extra_outputs(tcpServer)

target_include_directories(tcpServer PRIVATE ${CMAKE_CURRENT_LIST_DIR} )

target_link_libraries(tcpServer 
	pico_cyw43_arch_lwip_threadsafe_background
	pico_stdlib
	hardware_adc
)


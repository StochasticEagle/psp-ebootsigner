cmake_minimum_required(VERSION 3.20)

project(psp-ebootsigner VERSION 1.0.0 LANGUAGES C)

include(GNUInstallDirs)
include(CTest)

add_executable(ebootsign
    ebootsign.c
    crypto.c
    kirk_engine.c
    pack-pbp.c
    unpack-pbp.c
    fix-realocations.c
)

target_compile_features(ebootsign PRIVATE c_std_99)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(ebootsign PRIVATE
        -Wall
        -Wextra
        -Werror
        -Wno-unused-parameter
    )
endif()

install(TARGETS ebootsign
    RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
)

if(BUILD_TESTING)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)

    add_test(
        NAME ebootsign-structure
        COMMAND
            "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_ebootsign.py"
            "$<TARGET_FILE:ebootsign>"
    )
endif()

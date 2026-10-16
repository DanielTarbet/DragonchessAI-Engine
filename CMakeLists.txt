cmake_minimum_required(VERSION 3.15)
project(Dragonchess VERSION 1.0.0 LANGUAGES CXX)

if(WIN32)
    find_package(dlfcn-win32 CONFIG REQUIRED)
    set(PLATFORM_DL_LIBS dlfcn-win32::dl)
else()
    set(PLATFORM_DL_LIBS ${CMAKE_DL_LIBS})
endif()


set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
option(HEADLESS_ONLY "Build only the headless research binary" OFF)

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native")
endif()

include_directories(${CMAKE_SOURCE_DIR}/src)

if(HEADLESS_ONLY)
    set(SOURCES
        src/headless_main.cpp
        src/bitboard.cpp
        src/moves.cpp
        src/game.cpp
        src/ai.cpp
        src/td_features.cpp
        src/headless.cpp
        src/simple_ai.cpp
        src/ai_plugin.cpp
    )
else()
    find_package(SDL2 REQUIRED)
    find_package(SDL2_image REQUIRED)
    find_package(SDL2_ttf REQUIRED)

    include_directories(${SDL2_INCLUDE_DIRS})

    set(SOURCES
        src/main.cpp
        src/bitboard.cpp
        src/moves.cpp
        src/game.cpp
        src/ai.cpp
        src/td_features.cpp
        src/renderer.cpp
        src/input.cpp
        src/menu.cpp
        src/tournament.cpp
        src/campaign.cpp
        src/headless.cpp
        src/simple_ai.cpp
        src/ai_plugin.cpp
    )
endif()

add_executable(dragonchess ${SOURCES})

if(HEADLESS_ONLY)
    target_link_libraries(dragonchess
        ${PLATFORM_DL_LIBS}
    )
else()
    target_link_libraries(dragonchess
        ${SDL2_LIBRARIES}
        SDL2_image::SDL2_image
        SDL2_ttf::SDL2_ttf
        ${PLATFORM_DL_LIBS}
    )
endif()

add_executable(test_dragonchess
    src/test_game.cpp
    src/bitboard.cpp
    src/moves.cpp
    src/game.cpp
    src/ai.cpp
    src/td_features.cpp
)

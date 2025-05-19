"""Support for animated stickers"""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
from shutil import rmtree

from install_playwright import install
from PIL import Image
from playwright.sync_api import sync_playwright

THISDIR = str(Path(__file__).resolve().parent)


def convertLottie2ALL(fileName: str, newFileName: str, quality: int = 1, full_framerate: bool = True):
        """Convert to gif and webp

        Args:
        ----
                fileName (str): file path of the lottie file
                newFileName (str): name of the file to write (omit file ext)
                quality (int, optional): Quality of the returned sequence. Defaults to 1.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        """
        convertMultLottie2ALL([fileName], [newFileName], quality, full_framerate)


def convertLottie2GIF(fileName: str, newFileName: str, quality: int = 1, full_framerate: bool = True):
        """Convert to gif

        Args:
        ----
                fileName (str): file path of the lottie file
                newFileName (str): name of the file to write
                quality (int, optional): Quality of the returned sequence. Defaults to 1.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        """
        convertMultLottie2GIF([fileName], [newFileName], quality, full_framerate)


def convertLottie2Webp(fileName: str, newFileName: str, quality: int = 1, full_framerate: bool = True):
        """Convert to webp

        Args:
        ----
                fileName (str): file path of the lottie file
                newFileName (str): name of the file to write
                quality (int, optional): Quality of the returned sequence. Defaults to 1.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        """
        convertMultLottie2Webp([fileName], [newFileName], quality, full_framerate)


def convertMultLottie2ALL(fileNames: list[str], newFileNames: list[str], quality: int = 1, full_framerate: bool = True):
        """Convert to gif and webp

        Args:
        ----
                fileNames (list[str]): list of file path to the lottie files
                newFileNames (list[str]): name of the files to write (omit file ext)
                quality (int, optional): Quality of the returned sequence. Defaults to 1.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        """
        imageDataList = convertLotties2PIL(fileNames, quality, full_framerate)
        for index, imageData in enumerate(imageDataList):
                images = imageData[0]
                duration = imageData[1]
                images[0].save(
                        newFileNames[index] + ".gif",
                        append_images=images[1:],
                        duration=duration * 1000 / len(images),
                        version="GIF89a",
                        transparency=0,
                        disposal=2,
                        save_all=True,
                        loop=0,
                )
                images[0].save(
                        newFileNames[index] + ".webp",
                        save_all=True,
                        append_images=images[1:],
                        duration=int(duration * 1000 / len(images)),
                        loop=0,
                )
        rmtree("temp", ignore_errors=True)


def convertMultLottie2GIF(fileNames: list[str], newFileNames: list[str], quality: int = 1, full_framerate: bool = True):
        """Convert to gif

        Args:
        ----
                fileNames (list[str]): list of file path to the lottie files
                newFileNames (list[str]): name of the files to write
                quality (int, optional): Quality of the returned sequence. Defaults to 1.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        """
        imageDataList = convertLotties2PIL(fileNames, quality, full_framerate)
        for index, imageData in enumerate(imageDataList):
                images = imageData[0]
                duration = imageData[1]
                images[0].save(
                        newFileNames[index],
                        save_all=True,
                        append_images=images[1:],
                        duration=duration * 1000 / len(images),
                        loop=0,
                        transparency=0,
                        disposal=2,
                )
        rmtree("temp", ignore_errors=True)


def convertMultLottie2Webp(fileNames: list[str], newFileNames: list[str], quality: int = 1, full_framerate: bool = True):
        """Convert to webp

        Args:
        ----
                fileNames (list[str]): list of file path to the lottie files
                newFileNames (list[str]): name of the files to write
                quality (int, optional): Quality of the returned sequence. Defaults to 1.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        """
        imageDataList = convertLotties2PIL(fileNames, quality, full_framerate)
        for index, imageData in enumerate(imageDataList):
                images = imageData[0]
                duration = imageData[1]
                images[0].save(
                        newFileNames[index],
                        save_all=True,
                        append_images=images[1:],
                        duration=int(duration * 1000 / len(images)),
                        loop=0,
                )
        rmtree("temp", ignore_errors=True)


def _resQuality(quality: int, numFrames: int, duration: int):
        qualityMap = [10, 15, 20, 30]
        if quality >= len(qualityMap) or quality < 0:
                return 2
        return max(1, (numFrames // (duration * qualityMap[quality])))


def convertLotties2PIL(
        fileNames: list[str], quality: int = 1, full_framerate: bool = True
) -> list[tuple[list[Image.Image], float]]:
        """Convert list of lottie files to a list of images with a duration.

        Args:
        ----
                fileNames (list[str]): list of file paths of the lottie files
                quality (int, optional): Quality of the returned sequence. Defaults to 1.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        Returns:
        -------
                list[tuple[list[Image], float]]: pil images to write to gif/ webp and duration

        """
        lotties = []
        for fileName in fileNames:
                with open(fileName, "rb") as binfile:
                        magicNumber = binfile.read(2)
                        binfile.seek(0)
                        if magicNumber == b"\x1f\x8b":  # gzip magic number
                                try:
                                        archive = gzip.open(fileName, "rb")
                                        lottie = json.load(archive)
                                except gzip.BadGzipFile:
                                        continue
                        else:
                                lottie = json.loads(Path(fileName).read_text(encoding="utf-8"))
                lotties.append(lottie)
        frameData = recordLotties([json.dumps(lottie) for lottie in lotties], quality, lotties, full_framerate)

        imageDataList = []
        for index, frameDataInstance in enumerate(frameData):
                images = []
                duration = frameDataInstance[0]
                frames = frameDataInstance[1]  # List of frame numbers actually captured
                for frame in frames:
                        images.append(Image.open(f"temp/temp{index}_{frame}.png"))
                imageDataList.append([images, duration])
        return imageDataList


def recordLotties(lottieData: list[str], quality: int, lottieObjs: list[dict], full_framerate: bool = True) -> list[list[int]]:
        """Record the lottie data to a set of images

        Args:
        ----
                lottieData (str): lottie data as string
                quality (int, optional): Quality of the returned sequence.
                full_framerate (bool, optional): Export all frames. Defaults to True.

        Returns:
        -------
                list[list[int]]: duration and list of frame numbers

        """
        # Make temp dir
        if os.path.isdir("temp"):
                pass
        else:
                os.mkdir("temp")
        with sync_playwright() as p:
                install(p.chromium)
                browser = p.chromium.launch()

                frameData = [
                        recordSingleLottie(browser, lottieDataInstance, quality, index, lottieObjs[index], full_framerate)
                        for index, lottieDataInstance in enumerate(lottieData)
                ]

                browser.close()

        return frameData


def recordSingleLottie(browser, lottieDataInstance, quality, index, lottieObj, full_framerate: bool = True) -> list[int]:
        page = browser.new_page()
        html = (
                Path(THISDIR + "/lottie.html")
                .read_text(encoding="utf-8")
                .replace("lottieData", lottieDataInstance)
                .replace("WIDTH", str(lottieObj["w"]))
                .replace("HEIGHT", str(lottieObj["h"]))
        )
        page.set_content(html)
        duration = page.evaluate("() => duration")

        # Use lottie JSON ip/op for frame range
        ip = int(lottieObj.get("ip", 0))
        op = int(lottieObj.get("op", 0))
        numFrames = op - ip  # total number of frames

        if full_framerate:
                frames_to_capture = list(range(ip, op))  # Capture every frame!
                step = 1
        else:
                step = _resQuality(quality, numFrames, duration)
                frames_to_capture = list(range(ip, op, step))
                if frames_to_capture and frames_to_capture[-1] != (op - 1):
                        frames_to_capture.append(op - 1)  # ensure last frame is captured

        rootHandle = page.main_frame.wait_for_selector("#root")

        for frame in frames_to_capture:
                page.evaluate(f"animation.goToAndStop({frame}, true)")
                page.wait_for_timeout(20)  # Give time for renderer to update
                rootHandle.screenshot(path=f"temp/temp{index}_{frame}.png", omit_background=True)
        page.close()
        return [duration, frames_to_capture, step]

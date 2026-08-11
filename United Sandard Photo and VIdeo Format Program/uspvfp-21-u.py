# UNITED STANDARD VIDEO & PHOTO FORMAT PROGRAM (PYTHON 3)
# VERSION 21
# CHANGES FROM VERSION 17:
#   - FIX 1 & 2 : GetStartingCount() — counter dimulai dari angka tertinggi yang sudah ada
#   - FIX 3     : BatchRenameToTemp() — semua file digit di-rename ke temp secara batch sebelum konversi
#   - FIX 4 & 5 : Progress log JSON — crash recovery dan resume otomatis
#   - FIX 6 & 9 : Semua file (digit & non-digit) pakai pola temp — file asli aman sampai output selesai

# 1 IMPORT LIBRARY
# 1.1 IMPORT BUILD-IN LIBRARY
import os
import json
import pathlib
import re
# 1.2 IMPORT EXTERNAL LIBRARY
try:
	import ffmpeg
	from PIL import Image
	from pillow_heif import register_heif_opener
	register_heif_opener()

# 1.3 ERROR MODULE NOT FOUND HANDLING
except ModuleNotFoundError:
	print("[!] Module Not Found Error, try \"pip install ffmpeg-python pillow\"")
	exit()

# 2 DEFINE VARIABLE
# 2.1 DEFINE FOLDER AND RESOLUTION VARIABLE
DEFAULT_WORKING_DIRECTORY     = pathlib.Path('.')
DEFAULT_SHORT_SIDE_RESOLUTION = 720 # 1080 FOR BETTER RESOLUTION
# 2.2 DEFINE FILE FORMAT VARIABLE
SCAN_PHOTO_FORMAT             = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff',  '.gif', '.heic'}
SCAN_VIDEO_FORMAT             = {'.mp4',  '.mkv', '.mov', '.avi',  '.flv',  '.wmv', '.webm', '.ts', '.m4v'}
SCAN_ALL_FORMAT               = SCAN_PHOTO_FORMAT | SCAN_VIDEO_FORMAT
# 2.3 DEFINE PROGRESS LOG AND TEMP FILE PREFIX
PROGRESS_LOG_FILENAME         = '[_PROGRESS_].json'
TEMP_FILE_PREFIX              = '[_TEMP_]_'

# 3 DEFINE FUNCTION

# 3.1 SCAN WORKING DIRECTORY FUNCTION
def ScanDirectoryWithPathlib(ROOT_PATH):
	SCAN_RESULT = {}
	# 3.1.1 RECURSIVE SCAN WITH PATHLIB
	try:
		for FILE in ROOT_PATH.rglob('*'):
			try:
				# 3.1.2 FILTER NO FILE IN PATH
				if not FILE.is_file():
					continue
				# 3.1.3 FILTER NOT IN CONTEXT FILE FORMAT
				if not FILE.suffix.lower() in SCAN_ALL_FORMAT:
					continue
				# 3.1.4 FILTER TEMPORARY FILE
				if FILE.stem.startswith(TEMP_FILE_PREFIX):
					continue
				# 3.1.5 INSERT FILE INTO SCAN RESULT
				SCAN_RESULT.setdefault(FILE.parent, []).append(FILE)
			# 3.1.6 ERROR FILE PERMISSION DENIED HANDLING
			except PermissionError:
				print("[!] File %s Permission Denied Error" % str(FILE)[-64:])
	# 3.1.7 ERROR ROOT DIRECTORY PERMISSION DENIED HANDLING
	except PermissionError:
		print("[!] Root Directory Permission Denied Error")
		return SCAN_RESULT
	# 3.1.8 RETURN SECTION
	return SCAN_RESULT

# 3.2 CONVERT PHOTO WITH PILLOW
def ConvertPhotoWithPillow(INPUT_PATH, OUTPUT_PATH):
	# 3.2.1 OPEN IMAGE FILE WITH PILLOW
	try:
		INPUT_IMAGE_FILE = Image.open(INPUT_PATH)
	# 3.2.2 ERROR FILE NOT FOUND HANDLING
	except FileNotFoundError:
		print("[!] File %s Not Found Error" % str(INPUT_PATH)[-64:])
		# 3.2.3 RETURN ERROR FILE NOT FOUND
		return 3
	# 3.2.4 ERROR PERMISSION DENIED HANDLING
	except PermissionError:
		print("[!] File %s Permission Denied Error" % str(INPUT_PATH)[-64:])
		# 3.2.5 RETURN ERROR PERMISSION DENIED
		return 3
	# 3.2.6 GET IMAGE RESOLUTION
	try:
		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = INPUT_IMAGE_FILE.size
	except AttributeError:
		# 3.2.7 RETURN ERROR ATTRIBUTE
		return 3
	# 3.2.8 MAKE RESIZE SCALE
	IMAGE_SHORT_SIDE_RESOLUTION = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
	RESIZE_SCALE                = DEFAULT_SHORT_SIDE_RESOLUTION / IMAGE_SHORT_SIDE_RESOLUTION
	NEW_WIDTH                   = int(ORIGINAL_WIDTH  * RESIZE_SCALE)
	NEW_HEIGHT                  = int(ORIGINAL_HEIGHT * RESIZE_SCALE)
	# 3.2.9 FILTER STANDARD FILE (ALREADY SMALL ENOUGH)
	if IMAGE_SHORT_SIDE_RESOLUTION <= DEFAULT_SHORT_SIDE_RESOLUTION:
		# 3.2.10 RETURN SKIP FILE STANDARD
		return 2
	# 3.2.11 CHECK IF FILE IS ANIMATED GIF
	if getattr(INPUT_IMAGE_FILE, "is_animated", False):
		FRAME_LIST    = []
		DURATION_LIST = []
		# 3.2.12 FRAME LOOPING
		for FRAME_INDEX in range(INPUT_IMAGE_FILE.n_frames):
			INPUT_IMAGE_FILE.seek(FRAME_INDEX)
			# 3.2.13 RESIZE FRAME
			RESIZED_FRAME = INPUT_IMAGE_FILE.copy().resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
			# 3.2.14 INSERT RESIZED FRAME TO FRAME LIST
			FRAME_LIST.append(RESIZED_FRAME)
			# 3.2.15 ADD FRAME DURATION TO DURATION LIST
			try:
				DURATION_LIST.append(INPUT_IMAGE_FILE.info.get('duration', 100))
			# 3.2.16 ERROR NO DURATION HANDLING
			except AttributeError:
				DURATION_LIST.append(100)
		# 3.2.17 SAVE RESIZED GIF TO OUTPUT PATH
		FRAME_LIST[0].save(OUTPUT_PATH, save_all=True, append_images=FRAME_LIST[1:], duration=DURATION_LIST, loop=INPUT_IMAGE_FILE.info.get('loop', 0), optimize=False)
		# 3.2.18 RETURN GIF SUCCESS
		return 1
	# 3.2.19 NON GIF PHOTO RESIZE
	else:
		INPUT_IMAGE_FILE.resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS).save(OUTPUT_PATH)
		# 3.2.20 RETURN PHOTO SUCCESS
		return 1

# 3.3 CONVERT VIDEO WITH FFMPEG
def ConvertVideoWithFFMPEG(INPUT_PATH, OUTPUT_PATH):
	# 3.3.1 OPEN VIDEO FILE WITH FFPROBE
	try:
		PROBE_VIDEO = ffmpeg.probe(str(INPUT_PATH))
	# 3.3.2 ERROR FILE NOT FOUND HANDLING
	except FileNotFoundError:
		print("[!] File %s Not Found Error" % str(INPUT_PATH)[-64:])
		# 3.3.3 RETURN ERROR FILE NOT FOUND
		return 3
	# 3.3.4 ERROR PERMISSION DENIED HANDLING
	except PermissionError:
		print("[!] File %s Permission Denied Error" % str(INPUT_PATH)[-64:])
		# 3.3.5 RETURN ERROR PERMISSION DENIED
		return 3
	# 3.3.6 ERROR FFMPEG HANDLING
	except ffmpeg.Error:
		print("[!] File %s FFMPEG Error" % str(INPUT_PATH)[-64:])
		# 3.3.7 RETURN ERROR FROM FFMPEG
		return 3
	# 3.3.8 GET VIDEO STREAM INFORMATION
	try:
		VIDEO_STREAM = None
		# 3.3.9 FIND VIDEO STREAM
		for STREAM in PROBE_VIDEO['streams']:
			if STREAM['codec_type'] == 'video':
				VIDEO_STREAM = STREAM
				break
		# 3.3.10 FILTER NO VIDEO STREAM
		if VIDEO_STREAM is None:
			# 3.3.11 RETURN NO VIDEO STREAM
			return 3
		# 3.3.12 GET VIDEO RESOLUTION
		VIDEO_SHORT_SIDE = min(int(VIDEO_STREAM['width']), int(VIDEO_STREAM['height']))
		# 3.3.13 FILTER STANDARD FILE
		if VIDEO_SHORT_SIDE <= DEFAULT_SHORT_SIDE_RESOLUTION:
			# 3.3.14 RETURN SKIP STANDARD FILE
			return 2
		# 3.3.15 MAKE RESIZE SCALE
		RESIZE_SCALE = DEFAULT_SHORT_SIDE_RESOLUTION / VIDEO_SHORT_SIDE
		NEW_WIDTH    = int(int(VIDEO_STREAM['width'])  * RESIZE_SCALE)
		NEW_HEIGHT   = int(int(VIDEO_STREAM['height']) * RESIZE_SCALE)
		# 3.3.16 ROUND TO EVEN NUMBER (CODEC REQUIREMENT)
		NEW_WIDTH    = NEW_WIDTH  // 2 * 2
		NEW_HEIGHT   = NEW_HEIGHT // 2 * 2
		# 3.3.17 FFMPEG COMMAND
		input_stream = ffmpeg.input(str(INPUT_PATH))
		video = input_stream.video.filter("scale", NEW_WIDTH, NEW_HEIGHT)
		audio = input_stream.audio
		(
		    ffmpeg
		    .output(video, audio, str(OUTPUT_PATH), vcodec="libx264", acodec="aac", crf=18, preset="slow")
		    .run(overwrite_output=True, quiet=True)
		)
		# 3.3.18 RETURN VIDEO SUCCESS
		return 1
	# 3.3.19 ERROR FFMPEG HANDLING
	except ffmpeg.Error:
		print("[!] File %s FFMPEG Error" % str(INPUT_PATH)[-64:])
		# 3.3.20 RETURN FFMPEG ERROR
		return 3
	# 3.3.21 ERROR PERMISSION DENIED HANDLING
	except PermissionError:
		print("[!] File %s Permission Denied Error" % str(OUTPUT_PATH)[-64:])
		# 3.3.22 RETURN PERMISSION DENIED ERROR
		return 3

# 3.4 GET STARTING COUNT — FIX 1 & 2
# Cek file bernama angka yang sudah ada di folder, mulai count dari angka tertinggi + 1
# Tujuan: menghindari output baru menimpa file hasil konversi sesi sebelumnya
def GetStartingCount(FOLDER_PATH, EXTENSION):
	MAX_COUNT = 1
	try:
		for FILE in FOLDER_PATH.iterdir():
			if FILE.suffix.lower() == EXTENSION and FILE.stem.isdigit():
				MAX_COUNT = max(MAX_COUNT, int(FILE.stem) + 1)
	except PermissionError:
		pass
	return MAX_COUNT

# 3.5 BATCH RENAME TO TEMP — FIX 3
# Rename semua file digit ke nama temp SEKALIGUS sebelum konversi dimulai
# Tujuan: mencegah rename berantai error (misal 0.png -> 1.png tapi 1.png sudah ada)
def BatchRenameToTemp(FILE_LIST):
	RENAMED_MAP = {}  # { TEMP_PATH : FILE_PATH_ASLI }
	for FILE in FILE_LIST:
		if FILE.stem.isdigit() and FILE.exists():
			TEMP_FILE = FILE.parent / ('%s%s' % (TEMP_FILE_PREFIX, FILE.name))
			try:
				os.rename(FILE, TEMP_FILE)
				RENAMED_MAP[TEMP_FILE] = FILE
			except (PermissionError, FileNotFoundError, OSError) as e:
				print("[!] Gagal batch rename %s: %s" % (FILE.name, e))
	return RENAMED_MAP

# 3.6 LOAD PROGRESS LOG — FIX 4 & 5
# Baca progress dari JSON, jika ada. Digunakan untuk resume setelah crash.
def LoadProgressLog(FOLDER_PATH):
	LOG_PATH = FOLDER_PATH / PROGRESS_LOG_FILENAME
	try:
		if LOG_PATH.exists():
			with open(LOG_PATH, 'r') as F:
				return json.load(F)
	except Exception:
		pass
	return {}

# 3.7 SAVE PROGRESS LOG — FIX 4 & 5
# Tulis progress ke JSON. Dipanggil setiap kali status file berubah.
def SaveProgressLog(FOLDER_PATH, PROGRESS_DATA):
	LOG_PATH = FOLDER_PATH / PROGRESS_LOG_FILENAME
	try:
		with open(LOG_PATH, 'w') as F:
			json.dump(PROGRESS_DATA, F, indent=2)
	except Exception as e:
		print("[!] Gagal simpan progress log: %s" % e)

# 3.8 DELETE PROGRESS LOG — FIX 4 & 5
# Hapus file log setelah semua file di folder selesai diproses.
def DeleteProgressLog(FOLDER_PATH):
	LOG_PATH = FOLDER_PATH / PROGRESS_LOG_FILENAME
	try:
		if LOG_PATH.exists():
			os.remove(LOG_PATH)
	except Exception:
		pass

# 3.9 CONVERT AND RENAME LOGIC — GABUNGAN SEMUA FIX
def SortAndConvertAndRenameLogic(SCAN_FILE_LIST):
	SORT_RESULT = {}
	# 3.9.1 NATURAL SORT
	for FOLDER_NAME, FILE_LIST in SCAN_FILE_LIST.items():
		TEMPORARY_SORT = []
		# 3.9.2 LOOPING PER FILE
		for FILE in FILE_LIST:
			# 3.9.3 SPLIT FILE NAME WITH REGULAR EXPRESSION
			PART_NAME = re.split(r'(\d+)', FILE.name)
			SORT_KEY  = []
			# 3.9.4 BUILD SORT KEY
			for PART in PART_NAME:
				if PART.isdigit():
					SORT_KEY.append(int(PART))
				else:
					SORT_KEY.append(PART.lower())
			# 3.9.5 INSERT TO TEMPORARY SORT
			TEMPORARY_SORT.append((SORT_KEY, FILE))
		# 3.9.6 SORT
		TEMPORARY_SORT.sort()
		# 3.9.7 INSERT TO SORT RESULT
		for FILE in TEMPORARY_SORT:
			SORT_RESULT.setdefault(FOLDER_NAME, []).append(FILE[1])

	# 3.9.8 LOOPING PER FOLDER
	for FOLDER_NAME, FILE_LIST in SORT_RESULT.items():

		# 3.9.9 PRINT CURRENT FOLDER
		print("[+] %s" % FOLDER_NAME)

		# --- FIX 3: BATCH RENAME SEMUA FILE DIGIT KE TEMP SEBELUM PROSES APAPUN ---
		RENAMED_MAP = BatchRenameToTemp(FILE_LIST)
		# Update FILE_LIST: file yang sudah di-rename, ganti path-nya ke path temp
		UPDATED_FILE_LIST = []
		for FILE in FILE_LIST:
			POSSIBLE_TEMP = FILE.parent / ('%s%s' % (TEMP_FILE_PREFIX, FILE.name))
			if POSSIBLE_TEMP in RENAMED_MAP:
				UPDATED_FILE_LIST.append(POSSIBLE_TEMP)
			else:
				UPDATED_FILE_LIST.append(FILE)

		# --- FIX 1 & 2: MULAI COUNT DARI ANGKA TERTINGGI YANG SUDAH ADA ---
		PHOTO_COUNT = GetStartingCount(FOLDER_NAME, '.png')
		GIF_COUNT   = GetStartingCount(FOLDER_NAME, '.gif')
		VIDEO_COUNT = GetStartingCount(FOLDER_NAME, '.mp4')

		# --- FIX 4 & 5: LOAD PROGRESS LOG UNTUK RESUME ---
		PROGRESS = LoadProgressLog(FOLDER_NAME)

		# 3.9.10 LOOPING PER FILE
		for FILE in UPDATED_FILE_LIST:

			# --- FIX 4 & 5: SKIP FILE YANG SUDAH SELESAI ---
			FILE_KEY = FILE.name
			if PROGRESS.get(FILE_KEY) == 'done':
				print(" + [~] %s (sudah selesai, skip)" % FILE.name[-64:])
				continue

			# --- FIX 6 & 9: SEMUA FILE PAKAI POLA TEMP (bukan hanya yang digit) ---
			# Jika file belum di-rename ke temp (file non-digit), rename sekarang
			if not FILE.stem.startswith(TEMP_FILE_PREFIX):
				TEMP_FILE = FILE.parent / ('%s%s' % (TEMP_FILE_PREFIX, FILE.name))
				try:
					os.rename(FILE, TEMP_FILE)
				except (PermissionError, FileNotFoundError, OSError) as e:
					print("[!] Gagal rename %s ke temp: %s" % (FILE.name[-64:], e))
					continue
			else:
				# File digit sudah di-rename ke temp oleh BatchRenameToTemp
				TEMP_FILE = FILE
				# Nama aslinya adalah nama tanpa prefix temp
				FILE = FILE.parent / FILE.name[len(TEMP_FILE_PREFIX):]

			# --- FIX 4 & 5: TANDAI SEDANG DIPROSES ---
			PROGRESS[TEMP_FILE.name] = 'processing'
			SaveProgressLog(FOLDER_NAME, PROGRESS)

			# 3.9.11 FILTER GIF FILE
			if FILE.suffix.lower() == '.gif':
				OUTPUT_PATH = FOLDER_NAME / ('%s.gif' % GIF_COUNT)
				CONVERTION_RESULT = ConvertPhotoWithPillow(TEMP_FILE, OUTPUT_PATH)

				if CONVERTION_RESULT == 1:
					# Konversi berhasil: hapus temp
					try:
						os.remove(TEMP_FILE)
					except (PermissionError, FileNotFoundError) as e:
						print("[!] Gagal hapus temp %s: %s" % (TEMP_FILE.name[-64:], e))
						continue
					print(" + [+] %s --- %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
					GIF_COUNT += 1

				elif CONVERTION_RESULT == 2:
					# Skip (sudah kecil): rename temp ke output
					try:
						os.rename(TEMP_FILE, OUTPUT_PATH)
					except (PermissionError, FileNotFoundError, OSError) as e:
						print("[!] Gagal rename %s: %s" % (TEMP_FILE.name[-64:], e))
						os.rename(TEMP_FILE, FILE)
						continue
					print(" + [>] %s >>> %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
					GIF_COUNT += 1

				else:
					# Error: kembalikan temp ke nama asli
					try:
						os.rename(TEMP_FILE, FILE)
					except (PermissionError, FileNotFoundError, OSError) as e:
						print("[!] Gagal kembalikan %s: %s" % (TEMP_FILE.name[-64:], e))
					print(" + [!] %s XXX %s" % (FILE.name[-64:], FILE.name[-64:]))
					continue

			# 3.9.12 FILTER PHOTO FILE
			elif FILE.suffix.lower() in SCAN_PHOTO_FORMAT:
				OUTPUT_PATH = FOLDER_NAME / ('%s.png' % PHOTO_COUNT)
				CONVERTION_RESULT = ConvertPhotoWithPillow(TEMP_FILE, OUTPUT_PATH)

				if CONVERTION_RESULT == 1:
					# Konversi berhasil: hapus temp
					try:
						os.remove(TEMP_FILE)
					except (PermissionError, FileNotFoundError) as e:
						print("[!] Gagal hapus temp %s: %s" % (TEMP_FILE.name[-64:], e))
						continue
					print(" + [+] %s --- %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
					PHOTO_COUNT += 1

				elif CONVERTION_RESULT == 2:
					# Skip (sudah kecil): rename temp ke output
					try:
						os.rename(TEMP_FILE, OUTPUT_PATH)
					except (PermissionError, FileNotFoundError, OSError) as e:
						print("[!] Gagal rename %s: %s" % (TEMP_FILE.name[-64:], e))
						os.rename(TEMP_FILE, FILE)
						continue
					print(" + [>] %s >>> %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
					PHOTO_COUNT += 1

				else:
					# Error: kembalikan temp ke nama asli
					try:
						os.rename(TEMP_FILE, FILE)
					except (PermissionError, FileNotFoundError, OSError) as e:
						print("[!] Gagal kembalikan %s: %s" % (TEMP_FILE.name[-64:], e))
					print(" + [!] %s XXX %s" % (FILE.name[-64:], FILE.name[-64:]))
					continue

			# 3.9.13 FILTER VIDEO FILE
			elif FILE.suffix.lower() in SCAN_VIDEO_FORMAT:
				OUTPUT_PATH = FOLDER_NAME / ('%s.mp4' % VIDEO_COUNT)
				CONVERTION_RESULT = ConvertVideoWithFFMPEG(TEMP_FILE, OUTPUT_PATH)

				if CONVERTION_RESULT == 1:
					# Konversi berhasil: hapus temp
					try:
						os.remove(TEMP_FILE)
					except (PermissionError, FileNotFoundError) as e:
						print("[!] Gagal hapus temp %s: %s" % (TEMP_FILE.name[-64:], e))
						continue
					print(" + [+] %s --- %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
					VIDEO_COUNT += 1

				elif CONVERTION_RESULT == 2:
					# Skip (sudah kecil): rename temp ke output
					try:
						os.rename(TEMP_FILE, OUTPUT_PATH)
					except (PermissionError, FileNotFoundError, OSError) as e:
						print("[!] Gagal rename %s: %s" % (TEMP_FILE.name[-64:], e))
						os.rename(TEMP_FILE, FILE)
						continue
					print(" + [>] %s >>> %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
					VIDEO_COUNT += 1

				else:
					# Error: kembalikan temp ke nama asli
					try:
						os.rename(TEMP_FILE, FILE)
					except (PermissionError, FileNotFoundError, OSError) as e:
						print("[!] Gagal kembalikan %s: %s" % (TEMP_FILE.name[-64:], e))
					print(" + [!] %s XXX %s" % (FILE.name[-64:], FILE.name[-64:]))
					continue

			# --- FIX 4 & 5: TANDAI SELESAI DAN SIMPAN PROGRESS ---
			PROGRESS[TEMP_FILE.name] = 'done'
			SaveProgressLog(FOLDER_NAME, PROGRESS)

		# 3.9.14 HAPUS PROGRESS LOG SETELAH SEMUA FILE DI FOLDER SELESAI
		DeleteProgressLog(FOLDER_NAME)

# 4 MAIN PROGRAM
# 4.1 MAIN PROGRAM FUNCTION
def Main():
	# 4.1.1 CHECK DIRECTORY EXIST
	try:
		if not DEFAULT_WORKING_DIRECTORY.exists():
			print("[!] Direktori Tidak Ditemukan")
			return
		# 4.1.2 CHECK DIRECTORY IS DIRECTORY
		if not DEFAULT_WORKING_DIRECTORY.is_dir():
			print("[!] Direktori Tidak Valid")
			return
		# 4.1.3 START SCAN DIRECTORY
		print("[*] Scan Directory %s" % str(DEFAULT_WORKING_DIRECTORY.resolve())[-64:])
		SCAN_DIRECTORY_RESULT = ScanDirectoryWithPathlib(DEFAULT_WORKING_DIRECTORY)
		# 4.1.4 FILTER EMPTY SCAN RESULT
		if not SCAN_DIRECTORY_RESULT:
			print("[!] Empty Directory")
			return
		# 4.1.5 SORT, CONVERT, AND RENAME FILE
		SortAndConvertAndRenameLogic(SCAN_DIRECTORY_RESULT)
		# 4.1.6 PRINT ALL OPERATION END
		print("[*] All Operation Finish, Exit")
	# 4.1.7 ERROR KEYBOARD INTERRUPT HANDLING
	except KeyboardInterrupt:
		print("[!] Keyboard Interrupt")
		return

# 4.2 START PROGRAM
if __name__ == '__main__':
	Main()
# 4.3 END OF FILE
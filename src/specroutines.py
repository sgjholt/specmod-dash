"""
specroutines.py

	The file with functions to connect and manipulate SpecMod objects 
	for use with Dash.
"""
from SpecMod.specmod.Spectral import Spectra

def get_event_spectra(pdir: str, ev: str) -> Spectra:
	"""
	Loads in the spectra for a given local specmod event spectra group
	for a given event (datetime string).

	Args:
		pdir (str): The parent directory of the specmod spectra pickle file
		ev (str): The event datetime (e.g., "2012-10-08T12:12:12.760000Z")

	Returns:
		tr (specmod.Spectra): A SpecMod spectral instance
	"""
	E = f"{pdir}/{ev}/Spectra/{ev}.spec"
	sp = Spectra.read_spectra(E, skip_warning=True, method='pickle')
	return sp


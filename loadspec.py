"""

"""
from SpecMod.specmod.Spectral import Spectra


ev = "2012-10-08T12:12:12.760000Z"



def get_event_spectra(ev: str) -> Spectra:
	"""

	"""
	E = f"Events/{ev}/Spectra/{ev}.spec"
	sp = Spectra.read_spectra(E, skip_warning=True, method='pickle')
	print("loaded {}".format(E.split("/")[-1]))
	print(sp)
	return sp


if __name__ == "__main__":
	sp = get_event_spectra(ev)
	print(sp.get_spectra(sp.get_available_channels()[0]))
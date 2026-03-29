from django import forms
from .models import Product
from django.forms import modelformset_factory
from .models import Product, ProductImage, Brand, Category, SubCategory
# myshop/forms.py
from django import forms
from .models import Product, ProductImage, Category, SubCategory, Brand


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'


ProductImageFormSet = modelformset_factory(
    ProductImage,
    fields=('image',),
    extra=4,          # কয়টা gallery image চাই
    can_delete=True
)

class ProductImageForm(forms.ModelForm):
    """Form for individual product gallery images"""
    
    class Meta:
        model = ProductImage
        fields = ('image',)
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
                'accept': 'image/*'
            })
        }


ProductImageFormSet = forms.inlineformset_factory(
    Product, ProductImage, form=ProductImageForm,
    extra=4, max_num=10, can_delete=True
)
# Create formset for gallery images
ProductImageFormSet = forms.inlineformset_factory(
    Product,                    # Parent model
    ProductImage,               # Child model
    form=ProductImageForm,
    fields=('image',),
    extra=4,                    # Number of empty forms
    can_delete=True,            # Allow deletion
    max_num=10,                 # Maximum number of images
    validate_min=False,
    validate_max=True,
)


# Optional: Category, SubCategory, Brand forms for quick add
class QuickCategoryForm(forms.ModelForm):
    """Quick add category form"""
    class Meta:
        model = Category
        fields = ('name', 'description', 'icon')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'rows': 2,
                'placeholder': 'Optional description'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'fas fa-box'
            })
        }


class QuickSubCategoryForm(forms.ModelForm):
    """Quick add subcategory form"""
    class Meta:
        model = SubCategory
        fields = ('name', 'category', 'description', 'icon')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'Enter subcategory name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'rows': 2,
                'placeholder': 'Optional description'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'fas fa-folder'
            })
        }


class QuickBrandForm(forms.ModelForm):
    """Quick add brand form"""
    class Meta:
        model = Brand
        fields = ('name', 'tier', 'country', 'website')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'Enter brand name'
            }),
            'tier': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'e.g., USA'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'https://example.com'
            })
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500"
            }),
        }
class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['name', 'slug', 'category', 'description', 'icon', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-4 py-3.5 pl-11',
                'placeholder': 'Enter subcategory name'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-4 py-3.5 pl-11',
                'placeholder': 'Auto-generated slug'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-4 py-3.5 pl-11 appearance-none'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-4 py-3.5',
                'placeholder': 'Subcategory description',
                'rows': 3
            }),
            'icon': forms.Select(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-4 py-3.5 pl-11 appearance-none'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 px-4 py-3.5 text-center'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-slate-300 text-amber-600 focus:ring-amber-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        
        # Icon choices
        self.fields['icon'].choices = [
            ('fas fa-folder', '📁 Folder'),
            ('fas fa-tag', '🏷️ Tag'),
            ('fas fa-tags', '🏷️ Tags'),
            ('fas fa-box', '📦 Box'),
            ('fas fa-box-open', '📦 Open Box'),
            ('fas fa-cube', '⬛ Cube'),
            ('fas fa-cubes', '⬛ Cubes'),
            ('fas fa-laptop', '💻 Laptop'),
            ('fas fa-mobile-alt', '📱 Mobile'),
            ('fas fa-tshirt', '👕 T-Shirt'),
        ]
        
        # Help texts
        self.fields['slug'].help_text = 'URL-friendly version of the name'
        self.fields['order'].help_text = 'Lower numbers appear first'
        self.fields['slug'].required = False
    
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            # Auto-generate from name
            name = self.cleaned_data.get('name', '')
            if name:
                from django.utils.text import slugify
                slug = slugify(name)
        
        # Check for uniqueness
        qs = SubCategory.objects.filter(slug=slug)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError('This slug is already in use. Please choose a different one.')
        
        return slug
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        category = cleaned_data.get('category')
        
        if name and category:
            # Check for duplicate name within same category
            qs = SubCategory.objects.filter(name__iexact=name, category=category)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError(
                    f'A subcategory with name "{name}" already exists in {category.name}'
                )
        
        return cleaned_data


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-4 py-2',
                'placeholder': 'Enter brand name'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-slate-300 px-4 py-2',
                'placeholder': 'auto-generated or custom'
            }),
        }
